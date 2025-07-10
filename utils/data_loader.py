import pandas as pd
import pm4py
from datetime import datetime
import streamlit as st

class DataLoader:
    """Clase para cargar y procesar archivos CSV/Excel para process mining"""
    
    def __init__(self):
        pass
    
    def load_file(self, uploaded_file):
        """Cargar archivo CSV o Excel"""
        try:
            file_extension = uploaded_file.name.split('.')[-1].lower()
            
            if file_extension == 'csv':
                # Intentar diferentes encodings para CSV
                try:
                    df = pd.read_csv(uploaded_file, encoding='utf-8', low_memory=False)
                    #print(df.columns.tolist() ) # Forzar lectura de columnas
                except UnicodeDecodeError:
                    try:
                        uploaded_file.seek(0)
                        df = pd.read_csv(uploaded_file, encoding='latin-1')
                    except UnicodeDecodeError:
                        uploaded_file.seek(0)
                        df = pd.read_csv(uploaded_file, encoding='cp1252')
            
            elif file_extension in ['xlsx', 'xls']:
                df = pd.read_excel(uploaded_file)
            
            else:
                raise ValueError(f"Formato de archivo no soportado: {file_extension}")
            
            # Validaciones básicas
            if df.empty:
                raise ValueError("El archivo está vacío")
            
            if len(df.columns) < 4:
                raise ValueError("El archivo debe tener al menos 4 columnas para los campos obligatorios")
            
            return df
            
        except Exception as e:
            raise Exception(f"Error al cargar el archivo: {str(e)}")
    
    def validate_mapping(self, df, field_mapping):
        """Validar que el mapeo de campos es correcto"""
        errors = []
        
        # Verificar campos obligatorios
        required_fields = ['case_id', 'activity', 'start_time', 'end_time']
        for field in required_fields:
            if field not in field_mapping or field_mapping[field] is None:
                errors.append(f"Campo obligatorio '{field}' no mapeado")
            elif field_mapping[field] not in df.columns:
                errors.append(f"Columna '{field_mapping[field]}' no existe en el archivo")
        
        # Verificar que las columnas de fecha contengan datos válidos
        if field_mapping.get('start_time') and field_mapping.get('end_time'):
            start_col = field_mapping['start_time']
            end_col = field_mapping['end_time']
            
            # Verificar que no sean todo NaN
            if df[start_col].isna().all():
                errors.append(f"La columna de fecha de inicio '{start_col}' está vacía")
            
            if df[end_col].isna().all():
                errors.append(f"La columna de fecha de fin '{end_col}' está vacía")
        
        return errors
    
    def process_data(self, df, field_mapping):
        """Procesar datos y crear event log para pm4py"""
        try:
            # Validar mapeo
            validation_errors = self.validate_mapping(df, field_mapping)
            if validation_errors:
                raise ValueError("Errores de validación: " + "; ".join(validation_errors))
            
            # Crear copia de los datos
            processed_df = df.copy()
            
            # Crear event log según el formato esperado por pm4py
            # En lugar de duplicar eventos, vamos a usar solo los eventos de finalización
            # que representan la completación de cada actividad
            
            event_log_df = pd.DataFrame()
            
            # Mapear campos obligatorios
            event_log_df['case:concept:name'] = processed_df[field_mapping['case_id']].astype(str)
            event_log_df['concept:name'] = processed_df[field_mapping['activity']].astype(str)
            
            # Procesar fechas - usar solo la fecha de finalización como timestamp principal
            end_times = self.parse_timestamps(processed_df[field_mapping['end_time']])
            event_log_df['time:timestamp'] = end_times
            
            # Agregar lifecycle:transition como complete (actividad completada)
            event_log_df['lifecycle:transition'] = 'complete'
            
            # Agregar campos opcionales si están disponibles
            if field_mapping.get('cost'):
                cost_data = processed_df[field_mapping['cost']]
                event_log_df['cost:total'] = pd.to_numeric(cost_data, errors='coerce')
            
            if field_mapping.get('resource'):
                event_log_df['org:resource'] = processed_df[field_mapping['resource']].astype(str)
            
            # Agregar información de duración si tenemos fecha de inicio
            start_times = self.parse_timestamps(processed_df[field_mapping['start_time']])
            
            # Calcular duración de cada actividad
            duration_seconds = []
            for i in range(len(event_log_df)):
                if pd.notna(start_times.iloc[i]) and pd.notna(end_times.iloc[i]):
                    duration = (end_times.iloc[i] - start_times.iloc[i]).total_seconds()
                    duration_seconds.append(max(duration, 0))  # Evitar duraciones negativas
                else:
                    duration_seconds.append(0)
            
            event_log_df['activity:duration'] = duration_seconds
            
            # Usar event_log_df directamente como combined_events
            combined_events = event_log_df.copy()
            
            # Ordenar por caso y timestamp
            combined_events = combined_events.sort_values(['case:concept:name', 'time:timestamp'])
            combined_events = combined_events.reset_index(drop=True)
            
            # Eliminar filas con timestamps inválidos
            initial_count = len(combined_events)
            combined_events = combined_events.dropna(subset=['time:timestamp'])
            final_count = len(combined_events)
            
            if final_count == 0:
                raise Exception("No quedan eventos válidos después de limpiar timestamps inválidos")
            
            if final_count < initial_count * 0.5:
                print(f"Advertencia: Se eliminaron {initial_count - final_count} eventos con timestamps inválidos")
            
            # Validar que tenemos datos mínimos necesarios
            if len(combined_events) < 1:
                raise Exception("Se necesita al menos 1 evento para crear un event log válido")
            
            # Verificar que tenemos al menos un caso completo
            case_counts = combined_events['case:concept:name'].value_counts()
            if case_counts.max() < 1:
                raise Exception("Cada caso debe tener al menos 1 evento")
            
            # Convertir a event log de pm4py
            try:
                event_log = pm4py.convert_to_event_log(combined_events)
            except Exception as e:
                raise Exception(f"Error al convertir a event log de pm4py: {str(e)}")
            
            return combined_events, event_log
            
        except Exception as e:
            raise Exception(f"Error al procesar los datos: {str(e)}")
    
    def parse_timestamps(self, timestamp_series):
        """Convertir serie de timestamps a datetime"""
        try:
            # Intentar diferentes formatos de fecha
            parsed_timestamps = pd.to_datetime(timestamp_series, errors='coerce')
            
            # Si hay muchos valores nulos, intentar formatos específicos
            if parsed_timestamps.isna().sum() > len(parsed_timestamps) * 0.5:
                # Intentar formatos comunes
                formats = [
                    '%Y-%m-%d %H:%M:%S',
                    '%d/%m/%Y %H:%M:%S',
                    '%m/%d/%Y %H:%M:%S',
                    '%Y-%m-%d',
                    '%d/%m/%Y',
                    '%m/%d/%Y',
                    '%d-%m-%Y %H:%M:%S',
                    '%Y/%m/%d %H:%M:%S'
                ]
                
                for fmt in formats:
                    try:
                        parsed_timestamps = pd.to_datetime(timestamp_series, format=fmt, errors='coerce')
                        if parsed_timestamps.isna().sum() < len(parsed_timestamps) * 0.5:
                            break
                    except:
                        continue
            
            return parsed_timestamps
            
        except Exception as e:
            raise Exception(f"Error al parsear timestamps: {str(e)}")
    
    def get_data_summary(self, df):
        """Obtener resumen de los datos cargados"""
        summary = {
            'rows': len(df),
            'columns': len(df.columns),
            'column_names': df.columns.tolist(),
            'data_types': df.dtypes.to_dict(),
            'missing_values': df.isnull().sum().to_dict(),
            'sample_data': df.head().to_dict()
        }
        return summary
