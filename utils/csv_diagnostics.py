import pandas as pd
import streamlit as st
from io import StringIO

class CSVDiagnostics:
    """Utilidad para diagnosticar problemas en archivos CSV"""
    
    @staticmethod
    def analyze_csv_structure(uploaded_file):
        """Analizar la estructura de un archivo CSV problemático"""
        try:
            uploaded_file.seek(0)
            content = uploaded_file.read().decode('utf-8', errors='ignore')
            lines = content.split('\n')
            
            analysis = {
                'total_lines': len(lines),
                'non_empty_lines': len([line for line in lines if line.strip()]),
                'separators': {},
                'line_lengths': [],
                'problematic_lines': [],
                'encoding_issues': False
            }
            
            # Analizar separadores comunes
            separators = [',', ';', '\t', '|']
            for sep in separators:
                analysis['separators'][sep] = lines[0].count(sep) if lines else 0
            
            # Analizar longitud de líneas (número de campos)
            likely_separator = max(analysis['separators'], key=analysis['separators'].get)
            expected_fields = analysis['separators'][likely_separator] + 1
            
            for i, line in enumerate(lines[:50]):  # Analizar primeras 50 líneas
                if line.strip():
                    field_count = line.count(likely_separator) + 1
                    analysis['line_lengths'].append({
                        'line_number': i + 1,
                        'field_count': field_count,
                        'content_preview': line[:100]
                    })
                    
                    # Identificar líneas problemáticas
                    if field_count != expected_fields:
                        analysis['problematic_lines'].append({
                            'line_number': i + 1,
                            'expected_fields': expected_fields,
                            'actual_fields': field_count,
                            'content': line[:200]
                        })
            
            return analysis
            
        except UnicodeDecodeError:
            return {'encoding_issues': True, 'error': 'Problemas de codificación del archivo'}
        except Exception as e:
            return {'error': str(e)}
    
    @staticmethod
    def suggest_fixes(analysis):
        """Sugerir soluciones basadas en el análisis"""
        suggestions = []
        
        if analysis.get('encoding_issues'):
            suggestions.append("🔤 Problema de codificación: Guarde el archivo como CSV UTF-8")
        
        if analysis.get('problematic_lines'):
            suggestions.append("📊 Inconsistencia en número de campos:")
            for prob_line in analysis['problematic_lines'][:5]:  # Mostrar solo primeras 5
                suggestions.append(f"   - Línea {prob_line['line_number']}: esperaba {prob_line['expected_fields']} campos, encontró {prob_line['actual_fields']}")
        
        # Sugerir separador más probable
        if analysis.get('separators'):
            best_sep = max(analysis['separators'], key=analysis['separators'].get)
            if best_sep == ',':
                suggestions.append("✅ Separador detectado: coma (,)")
            elif best_sep == ';':
                suggestions.append("✅ Separador detectado: punto y coma (;)")
            elif best_sep == '\t':
                suggestions.append("✅ Separador detectado: tabulación")
        
        return suggestions
    
    @staticmethod
    def create_sample_csv():
        """Crear un CSV de ejemplo con el formato correcto"""
        sample_data = """case_id,activity,start_time,end_time,resource,cost
CASE001,Inicio,2024-01-01 09:00:00,2024-01-01 09:30:00,Juan,100
CASE001,Revision,2024-01-01 10:00:00,2024-01-01 11:00:00,Maria,150
CASE001,Aprobacion,2024-01-01 14:00:00,2024-01-01 14:15:00,Carlos,50
CASE002,Inicio,2024-01-02 08:00:00,2024-01-02 08:45:00,Ana,100
CASE002,Revision,2024-01-02 09:00:00,2024-01-02 10:30:00,Pedro,150"""
        
        return sample_data
    
    @staticmethod
    def show_diagnostic_interface(uploaded_file):
        """Mostrar interfaz de diagnóstico en Streamlit"""
        st.markdown("### 🔍 Diagnóstico del Archivo CSV")
        
        with st.spinner("Analizando estructura del archivo..."):
            analysis = CSVDiagnostics.analyze_csv_structure(uploaded_file)
        
        if analysis.get('error'):
            st.error(f"Error en el análisis: {analysis['error']}")
            return
        
        # Mostrar resultados del análisis
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**📊 Información General**")
            st.metric("Total de líneas", analysis.get('total_lines', 0))
            st.metric("Líneas no vacías", analysis.get('non_empty_lines', 0))
            
            if analysis.get('separators'):
                st.markdown("**🔗 Separadores Detectados**")
                for sep, count in analysis['separators'].items():
                    sep_name = {',' : 'Coma', ';': 'Punto y coma', '\t': 'Tabulación', '|': 'Pipe'}
                    st.text(f"{sep_name.get(sep, sep)}: {count}")
        
        with col2:
            if analysis.get('problematic_lines'):
                st.markdown("**⚠️ Líneas Problemáticas**")
                for prob_line in analysis['problematic_lines'][:3]:
                    st.error(f"Línea {prob_line['line_number']}: {prob_line['actual_fields']} campos (esperaba {prob_line['expected_fields']})")
        
        # Mostrar sugerencias
        suggestions = CSVDiagnostics.suggest_fixes(analysis)
        if suggestions:
            st.markdown("**💡 Sugerencias de Corrección**")
            for suggestion in suggestions:
                st.markdown(f"- {suggestion}")
        
        # Mostrar ejemplo de formato correcto
        with st.expander("📋 Ver ejemplo de formato correcto"):
            sample_csv = CSVDiagnostics.create_sample_csv()
            st.code(sample_csv, language='csv')
            
            # Botón para descargar ejemplo
            st.download_button(
                label="📥 Descargar CSV de ejemplo",
                data=sample_csv,
                file_name="ejemplo_process_mining.csv",
                mime="text/csv"
            )