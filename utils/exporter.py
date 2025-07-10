import json
import pandas as pd
import io
import base64
from datetime import datetime
from fpdf import FPDF
import tempfile
import os

class ResultExporter:
    """Clase para exportar resultados de análisis en diferentes formatos"""
    
    def __init__(self):
        self.temp_dir = tempfile.gettempdir()
    
    def export_to_pdf(self, export_data):
        """Exportar resultados a PDF"""
        try:
            pdf = FPDF()
            pdf.set_margins(15, 15, 15)  # Márgenes más amplios
            pdf.add_page()
            pdf.set_font('Arial', 'B', 16)
            
            # Título
            pdf.cell(0, 10, 'Reporte de Analisis de Procesos', 0, 1, 'C')
            pdf.ln(10)
            
            # Metadatos
            pdf.set_font('Arial', '', 10)
            metadata = export_data.get('metadata', {})
            pdf.cell(0, 8, f"Fecha de exportacion: {metadata.get('export_date', datetime.now().isoformat())}", 0, 1)
            pdf.cell(0, 8, f"Formato: {metadata.get('format', 'PDF')}", 0, 1)
            pdf.ln(5)
            
            # Resultados
            results = export_data.get('results', {})
            
            for section_name, section_data in results.items():
                if section_name.startswith('ai_'):
                    self._add_ai_section_to_pdf(pdf, section_name, section_data)
                elif section_name.startswith('viz_'):
                    self._add_visualization_section_to_pdf(pdf, section_name, section_data)
                else:
                    self._add_analysis_section_to_pdf(pdf, section_name, section_data)
            
            # Guardar PDF en memoria
            pdf_content = pdf.output(dest='S')
            
            # Si es bytearray (fpdf2 nueva versión), devolver directamente
            if isinstance(pdf_content, bytearray):
                return bytes(pdf_content)
            # Si es string (fpdf2 versión anterior), codificar
            elif isinstance(pdf_content, str):
                return pdf_content.encode('latin-1')
            else:
                return pdf_content
            
        except Exception as e:
            raise Exception(f"Error al exportar PDF: {str(e)}")
    
    def export_to_excel(self, export_data):
        """Exportar resultados a Excel"""
        try:
            output = io.BytesIO()
            
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                # Hoja de resumen
                summary_data = []
                metadata = export_data.get('metadata', {})
                summary_data.append(['Fecha de exportación', metadata.get('export_date', datetime.now().isoformat())])
                summary_data.append(['Formato', metadata.get('format', 'Excel')])
                summary_data.append(['Incluye visualizaciones', metadata.get('include_visualizations', False)])
                summary_data.append(['Incluye datos originales', metadata.get('include_raw_data', False)])
                
                summary_df = pd.DataFrame(summary_data, columns=['Campo', 'Valor'])
                summary_df.to_excel(writer, sheet_name='Resumen', index=False)
                
                # Hojas de análisis
                results = export_data.get('results', {})
                
                for section_name, section_data in results.items():
                    sheet_name = self._clean_sheet_name(section_name)
                    
                    if section_name == 'process':
                        self._export_process_analysis_to_excel(writer, section_data, sheet_name)
                    elif section_name == 'variants':
                        self._export_variants_analysis_to_excel(writer, section_data, sheet_name)
                    elif section_name == 'costs':
                        self._export_costs_analysis_to_excel(writer, section_data, sheet_name)
                    elif section_name == 'resources':
                        self._export_resources_analysis_to_excel(writer, section_data, sheet_name)
                    elif section_name == 'performance':
                        self._export_performance_analysis_to_excel(writer, section_data, sheet_name)
                    elif section_name.startswith('ai_'):
                        self._export_ai_analysis_to_excel(writer, section_data, sheet_name)
                
                # Datos originales si están incluidos
                if export_data.get('raw_data'):
                    raw_df = pd.DataFrame(export_data['raw_data'])
                    raw_df.to_excel(writer, sheet_name='Datos_Originales', index=False)
            
            output.seek(0)
            return output.getvalue()
            
        except Exception as e:
            raise Exception(f"Error al exportar Excel: {str(e)}")
    
    def export_to_csv(self, export_data):
        """Exportar resultados a CSV (archivo comprimido con múltiples CSVs)"""
        try:
            import zipfile
            
            zip_buffer = io.BytesIO()
            
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                # Metadata
                metadata = export_data.get('metadata', {})
                metadata_df = pd.DataFrame([metadata])
                metadata_csv = metadata_df.to_csv(index=False)
                zip_file.writestr('metadata.csv', metadata_csv)
                
                # Resultados de análisis
                results = export_data.get('results', {})
                
                for section_name, section_data in results.items():
                    filename = f"{section_name}.csv"
                    
                    if section_name in ['process', 'variants', 'costs', 'resources']:
                        # Convertir datos de análisis a DataFrame
                        if isinstance(section_data, dict):
                            # Aplanar el diccionario para CSV
                            flattened_data = self._flatten_dict(section_data)
                            df = pd.DataFrame([flattened_data])
                        else:
                            df = pd.DataFrame(section_data)
                        
                        csv_content = df.to_csv(index=False)
                        zip_file.writestr(filename, csv_content)
                    
                    elif section_name.startswith('ai_'):
                        # Análisis de IA
                        ai_data = []
                        if 'insights' in section_data:
                            for insight in section_data['insights']:
                                ai_data.append({'Type': 'Insight', 'Content': insight})
                        if 'recommendations' in section_data:
                            for rec in section_data['recommendations']:
                                ai_data.append({'Type': 'Recommendation', 'Content': rec})
                        
                        if ai_data:
                            ai_df = pd.DataFrame(ai_data)
                            csv_content = ai_df.to_csv(index=False)
                            zip_file.writestr(filename, csv_content)
                
                # Datos originales si están incluidos
                if export_data.get('raw_data'):
                    raw_df = pd.DataFrame(export_data['raw_data'])
                    raw_csv = raw_df.to_csv(index=False)
                    zip_file.writestr('datos_originales.csv', raw_csv)
            
            zip_buffer.seek(0)
            return zip_buffer.getvalue()
            
        except Exception as e:
            raise Exception(f"Error al exportar CSV: {str(e)}")
    
    def export_to_json(self, export_data):
        """Exportar resultados a JSON"""
        try:
            # Limpiar datos que no son serializables en JSON
            clean_data = self._clean_for_json(export_data)
            
            json_content = json.dumps(clean_data, indent=2, ensure_ascii=False, default=str)
            return json_content.encode('utf-8')
            
        except Exception as e:
            raise Exception(f"Error al exportar JSON: {str(e)}")
    
    def _add_ai_section_to_pdf(self, pdf, section_name, section_data):
        """Agregar sección de análisis con IA al PDF"""
        pdf.set_font('Arial', 'B', 12)
        title = section_name.replace('ai_', '').replace('_', ' ').title()
        pdf.cell(0, 8, f"Analisis con IA: {title}", 0, 1)
        pdf.ln(3)
        
        pdf.set_font('Arial', '', 10)
        
        if 'detailed_analysis' in section_data:
            pdf.multi_cell(0, 6, f"Analisis detallado: {section_data['detailed_analysis']}")
            pdf.ln(3)
        
        if 'insights' in section_data:
            pdf.cell(0, 6, "Insights principales:", 0, 1)
            for insight in section_data['insights'][:5]:  # Limitar a 5
                pdf.multi_cell(0, 6, f"- {insight}")
            pdf.ln(3)
        
        if 'recommendations' in section_data:
            pdf.cell(0, 6, "Recomendaciones:", 0, 1)
            for rec in section_data['recommendations'][:5]:  # Limitar a 5
                pdf.multi_cell(0, 6, f"- {rec}")
            pdf.ln(3)
        
        if 'optimizations' in section_data:
            pdf.cell(0, 6, "Optimizaciones:", 0, 1)
            for opt in section_data['optimizations'][:5]:  # Limitar a 5
                pdf.multi_cell(0, 6, f"- {opt}")
            pdf.ln(3)
        
        if 'improvements' in section_data:
            pdf.cell(0, 6, "Mejoras sugeridas:", 0, 1)
            for imp in section_data['improvements'][:5]:  # Limitar a 5
                pdf.multi_cell(0, 6, f"- {imp}")
        
        pdf.ln(5)
    
    def _add_visualization_section_to_pdf(self, pdf, section_name, section_data):
        """Agregar sección de visualización al PDF"""
        pdf.set_font('Arial', 'B', 12)
        title = section_name.replace('viz_', '').replace('_', ' ').title()
        pdf.cell(0, 8, f"Visualizacion: {title}", 0, 1)
        pdf.ln(3)
        
        pdf.set_font('Arial', '', 10)
        
        # Incluir imagen si existe
        if 'image_path' in section_data and section_data['image_path']:
            image_path = section_data['image_path']
            if os.path.exists(image_path):
                try:
                    # Agregar imagen al PDF
                    pdf.image(image_path, x=10, w=180)
                    pdf.ln(10)
                except Exception as e:
                    pdf.cell(0, 6, f"Error cargando imagen: {str(e)}", 0, 1)
                    pdf.ln(3)
        
        if 'metrics' in section_data:
            pdf.cell(0, 6, "Metricas del modelo:", 0, 1)
            for metric, value in section_data['metrics'].items():
                pdf.cell(0, 6, f"- {metric}: {value}", 0, 1)
            pdf.ln(5)
    
    def _add_analysis_section_to_pdf(self, pdf, section_name, section_data):
        """Agregar sección de análisis general al PDF"""
        pdf.set_font('Arial', 'B', 12)
        title = section_name.replace('_', ' ').title()
        pdf.cell(0, 8, f"Analisis: {title}", 0, 1)
        pdf.ln(3)
        
        pdf.set_font('Arial', '', 10)
        
        # Agregar métricas principales según el tipo de análisis
        if section_name == 'process':
            metrics = [
                f"Numero de casos: {section_data.get('num_cases', 'N/A')}",
                f"Numero de eventos: {section_data.get('num_events', 'N/A')}",
                f"Numero de actividades: {section_data.get('num_activities', 'N/A')}",
                f"Duracion promedio: {section_data.get('avg_case_duration', 'N/A')} dias"
            ]
            for metric in metrics:
                pdf.cell(0, 6, metric, 0, 1)
            pdf.ln(5)
            
        elif section_name == 'variants':
            pdf.cell(0, 6, f"Numero total de variantes: {section_data.get('num_variants', 'N/A')}", 0, 1)
            pdf.cell(0, 6, f"Variantes unicas: {section_data.get('unique_variants_count', 'N/A')}", 0, 1)
            pdf.ln(3)
            
            # Top variantes
            if 'top_variants' in section_data and section_data['top_variants']:
                pdf.cell(0, 6, "Top 5 variantes:", 0, 1)
                for i, variant in enumerate(section_data['top_variants'][:5]):
                    variant_name = variant.get('Variant', 'N/A')
                    # Truncar nombres de variantes muy largos
                    if len(variant_name) > 80:
                        variant_name = variant_name[:77] + "..."
                    try:
                        pdf.multi_cell(0, 5, f"{i+1}. {variant_name} ({variant.get('Cases', 0)} casos)")
                    except Exception:
                        # Si aún hay problemas, usar cell simple
                        pdf.cell(0, 5, f"{i+1}. Variante {i+1} ({variant.get('Cases', 0)} casos)", 0, 1)
            pdf.ln(5)
            
        elif section_name == 'costs':
            if section_data and 'cost_by_activity' in section_data:
                pdf.cell(0, 6, "Costos por actividad:", 0, 1)
                for cost_item in section_data['cost_by_activity'][:5]:
                    pdf.cell(0, 6, f"- {cost_item.get('Activity', 'N/A')}: ${cost_item.get('Total_Cost', 0):.2f}", 0, 1)
            elif section_data and 'total_cost' in section_data:
                pdf.cell(0, 6, f"Costo total del proceso: ${section_data.get('total_cost', 0):.2f}", 0, 1)
                pdf.cell(0, 6, f"Costo promedio por caso: ${section_data.get('avg_cost_per_case', 0):.2f}", 0, 1)
            else:
                pdf.cell(0, 6, "No hay datos de costos disponibles", 0, 1)
            pdf.ln(5)
            
        elif section_name == 'resources':
            if section_data and 'resource_workload' in section_data:
                pdf.cell(0, 6, "Carga de trabajo por recurso:", 0, 1)
                for resource in section_data['resource_workload'][:5]:
                    pdf.cell(0, 6, f"- {resource.get('Resource', 'N/A')}: {resource.get('Cases', 0)} casos", 0, 1)
            elif section_data and 'num_resources' in section_data:
                pdf.cell(0, 6, f"Numero total de recursos: {section_data.get('num_resources', 'N/A')}", 0, 1)
            else:
                pdf.cell(0, 6, "No hay datos de recursos disponibles", 0, 1)
            pdf.ln(5)
            
        elif section_name == 'performance':
            if 'duration_performance' in section_data:
                duration_perf = section_data['duration_performance']
                pdf.cell(0, 6, "Performance de duracion:", 0, 1)
                pdf.cell(0, 6, f"- Duracion ideal: {duration_perf.get('ideal_variant_duration', 'N/A')} dias", 0, 1)
                pdf.cell(0, 6, f"- Duracion promedio: {duration_perf.get('avg_process_duration', 'N/A')} dias", 0, 1)
                pdf.cell(0, 6, f"- Eficiencia: {duration_perf.get('performance_percentage', 'N/A')}%", 0, 1)
            pdf.ln(5)
    
    def _export_process_analysis_to_excel(self, writer, data, sheet_name):
        """Exportar análisis de proceso a Excel"""
        process_data = [
            ['Número de casos', data.get('num_cases', 'N/A')],
            ['Número de eventos', data.get('num_events', 'N/A')],
            ['Número de actividades', data.get('num_activities', 'N/A')],
            ['Duración promedio (días)', data.get('avg_case_duration', 'N/A')],
            ['Duración mínima (días)', data.get('min_case_duration', 'N/A')],
            ['Duración máxima (días)', data.get('max_case_duration', 'N/A')]
        ]
        
        df = pd.DataFrame(process_data, columns=['Métrica', 'Valor'])
        df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        # Agregar frecuencia de actividades si está disponible
        if 'activity_frequency' in data:
            activity_df = pd.DataFrame(data['activity_frequency'])
            activity_df.to_excel(writer, sheet_name=f"{sheet_name}_Actividades", index=False)
    
    def _export_variants_analysis_to_excel(self, writer, data, sheet_name):
        """Exportar análisis de variantes a Excel"""
        if data and 'top_variants' in data and data['top_variants']:
            variants_df = pd.DataFrame(data['top_variants'])
            variants_df.to_excel(writer, sheet_name=sheet_name, index=False)
        else:
            # Crear hoja con mensaje informativo
            empty_df = pd.DataFrame([['No hay datos de variantes disponibles']], columns=['Mensaje'])
            empty_df.to_excel(writer, sheet_name=sheet_name, index=False)
    
    def _export_costs_analysis_to_excel(self, writer, data, sheet_name):
        """Exportar análisis de costos a Excel"""
        if data and 'cost_by_activity' in data and data['cost_by_activity']:
            costs_df = pd.DataFrame(data['cost_by_activity'])
            costs_df.to_excel(writer, sheet_name=sheet_name, index=False)
        else:
            # Crear hoja con mensaje informativo
            empty_df = pd.DataFrame([['No hay datos de costos disponibles']], columns=['Mensaje'])
            empty_df.to_excel(writer, sheet_name=sheet_name, index=False)
    
    def _export_resources_analysis_to_excel(self, writer, data, sheet_name):
        """Exportar análisis de recursos a Excel"""
        if data and 'resource_workload' in data and data['resource_workload']:
            resources_df = pd.DataFrame(data['resource_workload'])
            resources_df.to_excel(writer, sheet_name=sheet_name, index=False)
        else:
            # Crear hoja con mensaje informativo
            empty_df = pd.DataFrame([['No hay datos de recursos disponibles']], columns=['Mensaje'])
            empty_df.to_excel(writer, sheet_name=sheet_name, index=False)
    
    def _export_performance_analysis_to_excel(self, writer, data, sheet_name):
        """Exportar análisis de performance a Excel"""
        performance_data = []
        
        # Performance por duración
        if 'duration_performance' in data:
            duration_perf = data['duration_performance']
            performance_data.extend([
                ['Métrica', 'Valor'],
                ['Duración Variante Ideal (días)', duration_perf.get('ideal_variant_duration', 'N/A')],
                ['Duración Promedio Proceso (días)', duration_perf.get('avg_process_duration', 'N/A')],
                ['Eficiencia de Duración (%)', duration_perf.get('performance_percentage', 'N/A')],
                ['Variante Más Eficiente', duration_perf.get('ideal_variant', 'N/A')]
            ])
        
        # Performance por costo
        if data.get('cost_performance'):
            cost_perf = data['cost_performance']
            performance_data.extend([
                ['', ''],
                ['Costo Variante Ideal', cost_perf.get('ideal_variant_cost', 'N/A')],
                ['Costo Promedio Proceso', cost_perf.get('avg_process_cost', 'N/A')],
                ['Eficiencia de Costo (%)', cost_perf.get('performance_percentage', 'N/A')],
                ['Variante Más Económica', cost_perf.get('ideal_cost_variant', 'N/A')]
            ])
        
        # Performance SLA
        if data.get('sla_performance'):
            sla_perf = data['sla_performance']
            performance_data.extend([
                ['', ''],
                ['Objetivo SLA (días)', sla_perf.get('target_days', 'N/A')],
                ['Casos Dentro SLA', sla_perf.get('cases_within_sla', 'N/A')],
                ['Total Casos', sla_perf.get('total_cases', 'N/A')],
                ['Cumplimiento SLA (%)', sla_perf.get('compliance_percentage', 'N/A')]
            ])
        
        if performance_data:
            performance_df = pd.DataFrame(performance_data)
            performance_df.to_excel(writer, sheet_name=sheet_name, index=False, header=False)
        
        # Comparación de variantes en una hoja separada
        if 'variant_duration_comparison' in data:
            comparison_df = pd.DataFrame(data['variant_duration_comparison'])
            comparison_df.to_excel(writer, sheet_name=f"{sheet_name}_Variantes", index=False)
    
    def _export_ai_analysis_to_excel(self, writer, data, sheet_name):
        """Exportar análisis de IA a Excel"""
        ai_data = []
        
        if 'insights' in data:
            for insight in data['insights']:
                ai_data.append({'Tipo': 'Insight', 'Contenido': insight})
        
        if 'recommendations' in data:
            for rec in data['recommendations']:
                ai_data.append({'Tipo': 'Recomendación', 'Contenido': rec})
        
        if ai_data:
            ai_df = pd.DataFrame(ai_data)
            ai_df.to_excel(writer, sheet_name=sheet_name, index=False)
    
    def _clean_sheet_name(self, name):
        """Limpiar nombre de hoja para Excel"""
        # Excel no permite ciertos caracteres en nombres de hojas
        clean_name = name.replace('/', '_').replace('\\', '_').replace('?', '_').replace('*', '_')
        clean_name = clean_name.replace('[', '_').replace(']', '_').replace(':', '_')
        return clean_name[:31]  # Excel limita a 31 caracteres
    
    def _flatten_dict(self, d, parent_key='', sep='_'):
        """Aplanar diccionario anidado para CSV"""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            elif isinstance(v, list):
                items.append((new_key, str(v)))
            else:
                items.append((new_key, v))
        return dict(items)
    
    def _clean_for_json(self, obj):
        """Limpiar objeto para serialización JSON"""
        if isinstance(obj, dict):
            return {k: self._clean_for_json(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._clean_for_json(item) for item in obj]
        elif hasattr(obj, '__dict__'):
            return str(obj)  # Convertir objetos complejos a string
        elif isinstance(obj, (datetime,)):
            return obj.isoformat()
        else:
            return obj
