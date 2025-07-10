import streamlit as st
import pandas as pd
import os
import json
from datetime import datetime
import traceback

# Importar módulos personalizados
from utils.data_loader import DataLoader 
from utils.process_analyzer import ProcessAnalyzer
from utils.visualizer import ProcessVisualizer
from utils.ai_analyzer import AIAnalyzer
from utils.exporter import ResultExporter
from utils.csv_diagnostics import CSVDiagnostics

st.set_page_config(
    page_title="Analizador de Procesos",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

def initialize_session_state():
    """Inicializar el estado de la sesión"""
    if 'data_loaded' not in st.session_state:
        st.session_state.data_loaded = False
    if 'mapped_data' not in st.session_state:
        st.session_state.mapped_data = None
    if 'event_log' not in st.session_state:
        st.session_state.event_log = None
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = {}

def main():
    initialize_session_state()
    
    st.header("**Analizador de Procesos**")
    st.markdown("**Aplicación de Process Mining para análisis de procesos de negocio**")
    st.divider()
    
    # Sidebar para navegación
    st.sidebar.title("Navegación")
    page = st.sidebar.selectbox(
        "Seleccionar sección:",
        ["Carga de Datos", "Mapeo de Campos", "Visión Preliminar", 
         "Análisis de Proceso", 
         "Análisis de Variantes", "Análisis de Costos", "Análisis de Recursos",
         "Análisis de Performance", "Visualizaciones", "Análisis con IA", "Exportar"]
    )
    
    if page == "Carga de Datos":
        show_data_loading()
    elif page == "Mapeo de Campos":
        show_field_mapping()
    elif page == "Visión Preliminar":
        show_process_overview()
    elif page == "Análisis de Proceso":
        show_process_analysis()
    elif page == "Análisis de Variantes":
        show_variant_analysis()
    elif page == "Análisis de Costos":
        show_cost_analysis()
    elif page == "Análisis de Recursos":
        show_resource_analysis()
    elif page == "Análisis de Performance":
        show_performance_analysis()
    elif page == "Visualizaciones":
        show_visualizations()
    elif page == "Análisis con IA":
        show_ai_analysis()
    elif page == "Exportar":
        show_export_results()

def show_data_loading():
    st.subheader("**📁 Carga de Datos**")
    st.markdown("Cargue su archivo CSV o Excel con los datos del proceso")
    
    uploaded_file = st.file_uploader(
        "Seleccionar archivo",
        type=['csv', 'xlsx', 'xls'],
        help="Formatos soportados: CSV, Excel (.xlsx, .xls)"
    )
    
    if uploaded_file is not None:
        try:
            with st.spinner("Cargando archivo..."):
                data_loader = DataLoader()
                df = data_loader.load_file(uploaded_file)
                
                st.success(f"Archivo cargado exitosamente: {len(df)} filas, {len(df.columns)} columnas")
                
                # Mostrar preview de los datos
                st.subheader("Vista previa de los datos")
                st.dataframe(df.head(10))
                
                # Mostrar información del dataset
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total de filas", len(df))
                with col2:
                    st.metric("Total de columnas", len(df.columns))
                with col3:
                    st.metric("Tamaño del archivo", f"{uploaded_file.size / 1024:.1f} KB")
                
                # Guardar en session state
                st.session_state.raw_data = df
                st.session_state.data_loaded = True
                
                st.success("Datos cargados correctamente. Proceda al 'Mapeo de Campos' para continuar.")
                
        except Exception as e:
            st.error(f"Error al cargar el archivo: {str(e)}")
            
            # Mostrar información de diagnóstico si está disponible
            error_str = str(e)
            if "Diagnóstico del archivo" in error_str:
                st.markdown("**Información de diagnóstico:**")
                st.text(error_str)
            else:
                with st.expander("Ver detalles técnicos del error"):
                    st.code(traceback.format_exc())
            
            # Mostrar consejos para resolver el problema
            st.markdown("**💡 Consejos para resolver el problema:**")
            st.markdown("""
            1. **Formato del archivo**: Asegúrese de que sea un CSV válido con separadores consistentes
            2. **Codificación**: Guarde el archivo como "CSV UTF-8" desde Excel
            3. **Datos con comas**: Si sus datos contienen comas, enciérrelos entre comillas dobles
            4. **Consistencia**: Todas las filas deben tener el mismo número de columnas
            5. **Caracteres especiales**: Evite caracteres especiales en los nombres de columnas
            """)
            
            # Opción para diagnóstico detallado
            st.markdown("**🔧 Opciones de recuperación:**")
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🔍 Diagnosticar Archivo", type="secondary"):
                    CSVDiagnostics.show_diagnostic_interface(uploaded_file)
            
            with col2:
                # Botón para descargar ejemplo
                sample_csv = CSVDiagnostics.create_sample_csv()
                st.download_button(
                    label="📋 Descargar Ejemplo CSV",
                    data=sample_csv,
                    file_name="ejemplo_process_mining.csv",
                    mime="text/csv"
                )

def show_field_mapping():
    st.subheader("**🔧 Mapeo de Campos**")
    
    if not st.session_state.data_loaded:
        st.warning("Primero debe cargar un archivo en la sección 'Carga de Datos'")
        return
    
    df = st.session_state.raw_data
    columns = df.columns.tolist()
    
    st.markdown("Mapee las columnas de su archivo con los campos requeridos para el análisis:")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Campos Obligatorios**")
        case_id = st.selectbox("ID del Caso", [""] + columns, help="Identificador único del caso")
        activity = st.selectbox("Actividad", [""] + columns, help="Nombre de la actividad/tarea")
        start_time = st.selectbox("Fecha de Inicio", [""] + columns, help="Timestamp de inicio del evento")
        end_time = st.selectbox("Fecha de Fin", [""] + columns, help="Timestamp de fin del evento")
    
    with col2:
        st.markdown("**Campos Opcionales**")
        cost = st.selectbox("Costo", [""] + columns, help="Costo asociado al evento")
        resource = st.selectbox("Recurso", [""] + columns, help="Recurso que ejecutó la actividad")
    
    # Validar mapeo
    required_fields = [case_id, activity, start_time, end_time]
    if all(field != "" for field in required_fields):
        if st.button("Procesar Datos", type="primary"):
            try:
                with st.spinner("Procesando datos..."):
                    data_loader = DataLoader()
                    
                    # Crear mapeo
                    field_mapping = {
                        'case_id': case_id,
                        'activity': activity,
                        'start_time': start_time,
                        'end_time': end_time,
                        'cost': cost if cost != "" else None,
                        'resource': resource if resource != "" else None
                    }
                    
                    # Procesar y crear event log
                    processed_df, event_log = data_loader.process_data(df, field_mapping)
                    
                    st.session_state.mapped_data = processed_df
                    st.session_state.event_log = event_log
                    st.session_state.field_mapping = field_mapping
                    
                    st.success("Datos procesados exitosamente")
                    
                    # Mostrar preview del event log
                    st.markdown("**Event Log Procesado**")
                    st.dataframe(processed_df.head(10))
                    
                    # Estadísticas básicas
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Casos únicos", processed_df['case:concept:name'].nunique())
                    with col2:
                        st.metric("Actividades únicas", processed_df['concept:name'].nunique())
                    with col3:
                        st.metric("Total eventos", len(processed_df))
                    with col4:
                        fecha_min = processed_df['time:timestamp'].min()
                        fecha_max = processed_df['time:timestamp'].max()
                        duracion = (fecha_max - fecha_min).days
                        st.metric("Duración (días)", duracion)
                    
            except Exception as e:
                st.error(f"Error al procesar los datos: {str(e)}")
                st.code(traceback.format_exc())
    else:
        st.warning("Complete todos los campos obligatorios para continuar")

def show_process_analysis():
    st.subheader("📈 Análisis de Proceso")
    
    if st.session_state.event_log is None:
        st.warning("Primero debe cargar y mapear los datos")
        return
    
    try:
        analyzer = ProcessAnalyzer()
        
        with st.spinner("Realizando análisis del proceso..."):
            results = analyzer.analyze_process(st.session_state.event_log)
            st.session_state.analysis_results['process'] = results
        
        # Mostrar resultados
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Estadísticas Generales**")
            st.metric("Número de casos", results['num_cases'])
            st.metric("Número de eventos", results['num_events'])
            st.metric("Número de actividades", results['num_activities'])
            st.metric("Duración promedio", f"{results['avg_case_duration']:.2f} días")
        
        with col2:
            st.markdown("**Actividades Principales**")
            activities_df = pd.DataFrame(results['activity_frequency'])
            st.dataframe(activities_df)
        
        # Gráfico de frecuencia de actividades
        st.markdown("**Frecuencia de Actividades**")
        if not activities_df.empty:
            st.bar_chart(activities_df.set_index('Activity')['Frequency'])
        
        # Distribución de duración de casos
        if 'case_durations' in results:
            st.markdown("**Distribución de Duración de Casos**")
            import plotly.express as px
            fig = px.histogram(
                x=results['case_durations'], 
                title="Distribución de Duración de Casos (días)",
                labels={'x': 'Duración (días)', 'y': 'Frecuencia'}
            )
            st.plotly_chart(fig)
        
    except Exception as e:
        st.error(f"Error en el análisis: {str(e)}")
        st.code(traceback.format_exc())
        st.markdown("**Distribución de Duración de Casos**")
        
        import plotly.express as px
        fig = px.histogram(
            x=results['case_durations'], 
            title="Distribución de Duración de Casos (días)",
            labels={'x': 'Duración (días)', 'y': 'Frecuencia'}
        )
        st.plotly_chart(fig)
        
    except Exception as e:
        st.error(f"Error en el análisis: {str(e)}")
        st.code(traceback.format_exc())

def show_variant_analysis():
    st.subheader("**🔄 Análisis de Variantes**")
    
    if st.session_state.event_log is None:
        st.warning("Primero debe cargar y mapear los datos")
        return
    
    try:
        analyzer = ProcessAnalyzer()
        
        with st.spinner("Analizando variantes del proceso..."):
            results = analyzer.analyze_variants(st.session_state.event_log)
            st.session_state.analysis_results['variants'] = results
        
        # Mostrar resultados
        st.markdown("**Variantes del Proceso**")
        st.metric("Número total de variantes", results['num_variants'])
        
        # Top variantes
        variants_df = pd.DataFrame(results['top_variants'])
        st.markdown("**Top 10 Variantes**")
        st.dataframe(variants_df)
        
        # Gráfico tipo ADN de variantes
        #st.markdown("**Gráfico ADN de Variantes**")
        if not variants_df.empty and 'Cases' in variants_df.columns:
            # Crear gráfico tipo ADN usando Plotly
            import plotly.graph_objects as go
            import plotly.express as px
            
            # Preparar datos para el gráfico ADN
            dna_data = []
            colors_palette = px.colors.qualitative.Set3
            
            display_variants = variants_df.head(15)  # Mostrar máximo 15 variantes
            for i in range(len(display_variants)):
                variant_name = f"Variante {i + 1}"
                variant_sequence = str(display_variants.iloc[i]['Variant'])
                cases_count = int(display_variants.iloc[i]['Cases'])
                percentage = float(display_variants.iloc[i]['Percentage'])
                
                # Dividir la secuencia en actividades individuales
                activities = variant_sequence.split(' -> ')
                
                # Crear fila para cada variante
                variant_row = {
                    'variant': variant_name,
                    'activities': activities,
                    'cases': cases_count,
                    'percentage': percentage,
                    'y_pos': len(display_variants) - i  # Posición vertical invertida
                }
                dna_data.append(variant_row)
            
            # Crear figura
            fig = go.Figure()
            
            # Obtener todas las actividades únicas para asignar colores consistentes
            all_activities = set()
            for variant in dna_data:
                all_activities.update(variant['activities'])
            
            activity_colors = {}
            for i, activity in enumerate(sorted(all_activities)):
                activity_colors[activity] = colors_palette[i % len(colors_palette)]
            
            # Agregar cada variante al gráfico
            for variant in dna_data:
                y_pos = variant['y_pos']
                x_positions = list(range(len(variant['activities'])))
                
                # Agregar cada actividad como un segmento
                for i, activity in enumerate(variant['activities']):
                    # Crear rectángulo para cada actividad
                    fig.add_shape(
                        type="rect",
                        x0=i - 0.4,
                        y0=y_pos - 0.4,
                        x1=i + 0.4,
                        y1=y_pos + 0.4,
                        fillcolor=activity_colors[activity],
                        line=dict(color="white", width=1),
                        opacity=0.8
                    )
                    
                    # Agregar texto de la actividad
                    fig.add_annotation(
                        x=i,
                        y=y_pos,
                        text=activity[:3].upper(),  # Mostrar solo las primeras 4 letras
                        showarrow=False,
                        font=dict(size=8, color="black"),
                        xanchor="center",
                        yanchor="middle"
                    )
                
                # Agregar información de la variante al lado izquierdo
                fig.add_annotation(
                    x=-1,
                    y=y_pos,
                    text=f"{variant['variant']}<br>{variant['cases']} casos<br>{variant['percentage']:.1f}%",
                    showarrow=False,
                    font=dict(size=10),
                    xanchor="right",
                    yanchor="middle",
                    bgcolor="rgba(255,255,255,0.8)",
                    bordercolor="gray",
                    borderwidth=1
                )
            
            # Configurar el layout
            max_activities = max(len(variant['activities']) for variant in dna_data) if dna_data else 1
            
            fig.update_layout(
                title="Gráfico ADN de Variantes del Proceso",
                xaxis=dict(
                    title="Secuencia de Actividades",
                    range=[-2, max_activities],
                    showgrid=False,
                    zeroline=False
                ),
                yaxis=dict(
                    title="Variantes",
                    range=[0, len(dna_data) + 1],
                    showgrid=False,
                    zeroline=False,
                    showticklabels=False
                ),
                height=50 * len(dna_data) + 100,  # Altura dinámica
                showlegend=False,
                plot_bgcolor='white',
                margin=dict(l=150, r=50, t=50, b=50)
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Leyenda de actividades
            st.markdown("Leyenda de Actividades")
            legend_cols = st.columns(min(4, len(all_activities)))
            for i, activity in enumerate(sorted(all_activities)):
                with legend_cols[i % len(legend_cols)]:
                    st.markdown(
                        f'<div style="display: flex; align-items: center;">'
                        f'<div style="width: 20px; height: 20px; background-color: {activity_colors[activity]}; '
                        f'border: 1px solid gray; margin-right: 8px;"></div>'
                        f'<span style="font-size: 8px;">{activity}</span>'
                        f'</div>',
                        unsafe_allow_html=True
                    )
        
        # Gráfico de distribución de variantes (adicional)
       # st.markdown("**Distribución de Variantes**")
       # if not variants_df.empty and 'Cases' in variants_df.columns:
            # Truncar nombres de variantes largas para mejor visualización
        #    display_df = variants_df.copy()
        #    display_df['Variant_Short'] = display_df['Variant'].apply(lambda x: x[:50] + '...' if len(x) > 50 else x)
         #   st.bar_chart(display_df.set_index('Variant_Short')['Cases'])
        
        # Análisis de conformidad


            st.markdown("")
        


        if 'conformance' in results:
            st.markdown("**Análisis de Conformidad**")
            conf_df = pd.DataFrame(results['conformance'])
            st.dataframe(conf_df)
        
    except Exception as e:
        st.error(f"Error en el análisis de variantes: {str(e)}")
        st.code(traceback.format_exc())

def show_cost_analysis():
    st.subheader("**💰 Análisis de Costos**")
    
    if st.session_state.event_log is None:
        st.warning("Primero debe cargar y mapear los datos")
        return
    
    # Verificar si hay datos de costo
    if st.session_state.field_mapping.get('cost') is None:
        st.warning("No se han mapeado datos de costo. Este análisis requiere información de costos.")
        return
    
    try:
        analyzer = ProcessAnalyzer()
        
        with st.spinner("Analizando costos..."):
            results = analyzer.analyze_costs(st.session_state.event_log)
            st.session_state.analysis_results['costs'] = results
        
        if results:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Estadísticas de Costos**")
                st.metric("Costo total", f"${results['total_cost']:,.0f}")
                st.metric("Costo promedio por caso", f"${results['avg_cost_per_case']:,.0f}")
                st.metric("Costo promedio por actividad", f"${results['avg_cost_per_activity']:,.0f}")
            
            with col2:
                st.markdown("**Costos por Actividad**")
                costs_df = pd.DataFrame(results['cost_by_activity'])
                st.dataframe(costs_df)
            
            # Gráfico de costos
            st.markdown("**Distribución de Costos por Actividad**")
            if not costs_df.empty and 'Total_Cost' in costs_df.columns:
                st.bar_chart(costs_df.set_index('Activity')['Total_Cost'])
            
        else:
            st.info("No se encontraron datos de costo válidos para analizar")
            
    except Exception as e:
        st.error(f"Error en el análisis de costos: {str(e)}")
        st.code(traceback.format_exc())

def show_resource_analysis():
    st.subheader("**👥 Análisis de Recursos**")
    
    if st.session_state.event_log is None:
        st.warning("Primero debe cargar y mapear los datos")
        return
    
    # Verificar si hay datos de recursos
    if st.session_state.field_mapping.get('resource') is None:
        st.warning("No se han mapeado datos de recursos. Este análisis requiere información de recursos.")
        return
    
    try:
        analyzer = ProcessAnalyzer()
        
        with st.spinner("Analizando recursos..."):
            results = analyzer.analyze_resources(st.session_state.event_log)
            st.session_state.analysis_results['resources'] = results
        
        if results:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Estadísticas de Recursos**")
                st.metric("Número total de recursos", results['num_resources'])
                st.metric("Actividades promedio por recurso", f"{results['avg_activities_per_resource']:.0f}")
            
            with col2:
                st.markdown("**Recursos más Activos**")
                resources_df = pd.DataFrame(results['resource_workload'])
                st.dataframe(resources_df)
            
            # Gráfico de carga de trabajo
            st.markdown("**Carga de Trabajo por Recurso**")
            if not resources_df.empty and 'Activities' in resources_df.columns:
                st.bar_chart(resources_df.set_index('Resource')['Activities'])
            
            # Matriz de recursos por actividad
            if 'resource_activity_matrix' in results:
                st.markdown("**Matriz Recurso-Actividad**")
                matrix_df = pd.DataFrame(results['resource_activity_matrix'])
                st.dataframe(matrix_df)
        else:
            st.info("No se encontraron datos de recursos válidos para analizar")
            
    except Exception as e:
        st.error(f"Error en el análisis de recursos: {str(e)}")
        st.code(traceback.format_exc())

def show_performance_analysis():
    st.subheader("**🚀 Análisis de Performance del Proceso**")
    
    if st.session_state.event_log is None:
        st.warning("Primero debe cargar y mapear los datos")
        return
    
    try:
        analyzer = ProcessAnalyzer()
        
        # Configuración de SLA
        st.markdown("**⚙️ Configuración de Análisis**")
        #col1, col2 = st.columns(2)
        
       # with col1:
       #     enable_sla = st.checkbox("Activar análisis de SLA", value=False)
        
       # with col2:
       #     sla_target = None
       #     if enable_sla:
       #         sla_target = st.number_input(
        #            "Objetivo SLA (días)", 
        #            min_value=0.1, 
         #           value=5.0, 
          #          step=0.1,
          #          help="Tiempo objetivo para completar un caso"
         #       )
        
        if st.button("Realizar Análisis de Performance", type="primary", on_click= None):
            with st.spinner("Analizando performance del proceso..."):
                try:
                    results = analyzer.analyze_performance(st.session_state.event_log, None)
                    st.session_state.analysis_results['performance'] = results
                    
                    # Mostrar resultados
                    st.success("Análisis de performance completado")
                    
                except Exception as analysis_error:
                    st.error(f"Error en el análisis de performance: {str(analysis_error)}")
                    
                    # Mostrar información de debug si está disponible
                    if st.session_state.event_log is not None:
                        with st.expander("🔍 Información de debug del event log"):
                            st.write(f"**Número de trazas:** {len(st.session_state.event_log)}")
                            if len(st.session_state.event_log) > 0:
                                first_trace = st.session_state.event_log[0]
                                st.write(f"**Eventos en primera traza:** {len(first_trace)}")
                                if len(first_trace) > 0:
                                    first_event = first_trace[0]
                                    st.write(f"**Campos disponibles:** {list(first_event.keys())}")
                    
                    st.info("Sugerencias para resolver el error:")
                    st.write("• Verificar que los datos de fecha están en formato correcto")
                    st.write("• Asegurar que hay al menos 2 eventos por caso")
                    st.write("• Revisar que no hay valores faltantes en campos obligatorios")
                    st.write("• Intentar cargar de nuevo los datos con un mapeo diferente")
                    return
            
            # Métricas de performance por duración
            st.markdown("**⏱️ Performance por Duración**")
            duration_perf = results['duration_performance']
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric(
                    "Duración Variante Ideal", 
                    f"{duration_perf['ideal_variant_duration']:.1f} días"
                )
            with col2:
                st.metric(
                    "Duración Promedio Proceso", 
                    f"{duration_perf['avg_process_duration']:.1f} días"
                )
            with col3:
                st.metric(
                    "Desempeño del Proceso", 
                    f"{duration_perf['performance_ratio']:.1f}",
                    help="Duración variante ideal / Duración promedio proceso"
                )
            with col4:
                st.metric(
                    "Porcentaje de Eficiencia", 
                    f"{duration_perf['performance_percentage']:.1f}%",
                    delta=f"{duration_perf['performance_percentage'] - 100:.1f}%"
                )
            
            st.info(f"**Variante más eficiente:** {duration_perf['ideal_variant']}")
            
            # Explicación del desempeño
            with st.expander("📊 ¿Cómo interpretar el desempeño del proceso?"):
                st.write("**Desempeño del Proceso = Duración de la variante ideal / Duración promedio del proceso**")
                st.write(f"• **Valor calculado:** {duration_perf['performance_ratio']:.1f}")
                st.write("• **Interpretación:**")
                if duration_perf['performance_ratio'] < 0.5:
                    st.error("🔴 Performance baja: La variante ideal es mucho más rápida que el promedio")
                elif duration_perf['performance_ratio'] < 0.8:
                    st.warning("🟡 Performance media: Hay oportunidades de mejora significativas")
                else:
                    st.success("🟢 Performance alta: El proceso es relativamente eficiente")
                
                st.write("• **Ejemplo:** Si el valor es 0.5, significa que la variante ideal toma la mitad del tiempo que el promedio del proceso")
                st.write("• **Valores más bajos indican mayor potencial de optimización**")
            
            # Métricas de performance por costo
            if results['cost_performance']:
                st.markdown("**💰 Performance por Costo**")
                cost_perf = results['cost_performance']
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric(
                        "Costo Variante Ideal", 
                        f"${cost_perf['ideal_variant_cost']:,.0f}"
                    )
                with col2:
                    st.metric(
                        "Costo Promedio Proceso", 
                        f"${cost_perf['avg_process_cost']:,.0f}"
                    )
                with col3:
                    st.metric(
                        "Desempeño por Costo", 
                        f"{cost_perf['performance_ratio']:.1f}",
                        help="Costo variante ideal / Costo promedio proceso"
                    )
                with col4:
                    st.metric(
                        "Porcentaje de Eficiencia", 
                        f"{cost_perf['performance_percentage']:.1f}%",
                        delta=f"{cost_perf['performance_percentage'] - 100:.1f}%"
                    )
                
                st.info(f"**Variante más económica:** {cost_perf['ideal_cost_variant']}")
                
                # Explicación del desempeño por costo
                with st.expander("💰 ¿Cómo interpretar el desempeño por costo?"):
                    st.write("**Desempeño por Costo = Costo de la variante ideal / Costo promedio del proceso**")
                    st.write(f"• **Valor calculado:** {cost_perf['performance_ratio']:.1f}")
                    st.write("• **Interpretación:**")
                    if cost_perf['performance_ratio'] < 0.5:
                        st.error("🔴 Performance baja: La variante ideal cuesta mucho menos que el promedio")
                    elif cost_perf['performance_ratio'] < 0.8:
                        st.warning("🟡 Performance media: Hay oportunidades de ahorro significativas")
                    else:
                        st.success("🟢 Performance alta: Los costos del proceso son relativamente eficientes")
                    
                    st.write("• **Ejemplo:** Si el valor es 0.6, significa que la variante ideal cuesta el 60% del costo promedio")
                    st.write("• **Valores más bajos indican mayor potencial de ahorro de costos**")
            else:
                st.info("No hay datos de costo disponibles para análisis de performance por costo")
            
            # Métricas de SLA
            if results['sla_performance']:
                st.subheader("📊 Performance de SLA")
                sla_perf = results['sla_performance']
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Objetivo SLA", f"{sla_perf['target_days']} días")
                with col2:
                    st.metric("Casos Dentro SLA", sla_perf['cases_within_sla'])
                with col3:
                    st.metric("Total Casos", sla_perf['total_cases'])
                with col4:
                    st.metric(
                        "Cumplimiento SLA", 
                        f"{sla_perf['compliance_percentage']:.1f}%",
                        delta=f"{sla_perf['compliance_percentage'] - 100:.1f}%" if sla_perf['compliance_percentage'] < 100 else "✓"
                    )
                
                # Gráfico de torta para SLA
                import plotly.express as px
                sla_data = {
                    'Estado': ['Dentro de SLA', 'Fuera de SLA'],
                    'Casos': [sla_perf['cases_within_sla'], sla_perf['cases_over_sla']]
                }
                fig_sla = px.pie(
                    values=sla_data['Casos'], 
                    names=sla_data['Estado'],
                    title="Distribución de Cumplimiento de SLA",
                    color_discrete_map={'Dentro de SLA': '#2E8B57', 'Fuera de SLA': '#DC143C'}
                )
                st.plotly_chart(fig_sla)
            
            # Comparación de duración por variante
            #st.markdown("**📈 Comparación de Duración Promedio por Variante**")
            
            variant_comparison = results['variant_duration_comparison']
            if variant_comparison:
                # Preparar datos para el gráfico
                import pandas as pd
                df_variants = pd.DataFrame(variant_comparison)
                
                # Mostrar tabla de comparación
              #  st.dataframe(df_variants.round(2))
                
                # Gráfico de barras de duración promedio por variante
               # import plotly.express as px
                
                # Limitar a top 10 variantes para mejor visualización
                df_top = df_variants.head(10).copy()
              #  df_top['Variante_Short'] = df_top['Variante'].apply(
              #      lambda x: x[:30] + '...' if len(x) > 30 else x
              #  )
                
              #  fig_duration = px.bar(
               #     df_top,
                #    x='Variante_Short',
                 #   y='Duración_Promedio',
                  #  title='Duración Promedio por Variante (Top 10)',
                   # labels={
                   #     'Variante_Short': 'Variante del Proceso',
                   #     'Duración_Promedio': 'Duración Promedio (días)'
                   # },
                   # color='Duración_Promedio',
                   # color_continuous_scale='RdYlGn_r'
                #)
              #  fig_duration.update_layout(
               #     xaxis_tickangle=-45,
               #     height=500
               # )
               # st.plotly_chart(fig_duration, use_container_width=True)
                
                # Gráfico de dispersión duración vs casos
              #  fig_scatter = px.scatter(
              #      df_variants,
              #      x='Casos',
              #      y='Duración_Promedio',
              #      size='Desviación_Estándar',
              #      hover_data=['Variante'],
              #      title='Relación entre Número de Casos y Duración Promedio',
              #      labels={
               #         'Casos': 'Número de Casos',
               #         'Duración_Promedio': 'Duración Promedio (días)',
               #         'Desviación_Estándar': 'Desviación Estándar'
               #     }
               # )
               # st.plotly_chart(fig_scatter, use_container_width=True)
                
                # Análisis de insights
                st.markdown("**💡 Insights de Performance**")
                
                best_variant = df_variants.iloc[0]
                worst_variant = df_variants.iloc[-1]
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.success("**Mejor Performance**")
                    st.write(f"**Variante:** {best_variant['Variante']}")
                    st.write(f"**Duración:** {best_variant['Duración_Promedio']:.1f} días")
                    st.write(f"**Casos:** {best_variant['Casos']}")
                
                with col2:
                    st.error("**Peor Performance")
                    st.write(f"**Variante:** {worst_variant['Variante']}")
                    st.write(f"**Duración:** {worst_variant['Duración_Promedio']:.1f} días")
                    st.write(f"**Casos:** {worst_variant['Casos']}")
                
                # Oportunidades de mejora
                improvement_potential = ((worst_variant['Duración_Promedio'] - best_variant['Duración_Promedio']) / worst_variant['Duración_Promedio']) * 100
                st.info(f"**Potencial de mejora:** {improvement_potential:.1f}% reducción en tiempo si se optimizan las variantes menos eficientes")
            
    except Exception as e:
        st.error(f"Error en el análisis de performance: {str(e)}")
        st.code(traceback.format_exc())

def show_process_overview():
    st.subheader("**Visión Preliminar del Proceso**")
    
    if st.session_state.event_log is None:
        st.warning("Primero debe cargar y mapear los datos")
        return
    
    # Imports necesarios
    import plotly.graph_objects as go
    import plotly.express as px
    
    try:
        # Obtener análisis básico si no existe
        if 'process' not in st.session_state.analysis_results:
            analyzer = ProcessAnalyzer()
            with st.spinner("Generando análisis preliminar..."):
                results = analyzer.analyze_process(st.session_state.event_log)
                st.session_state.analysis_results['process'] = results
        
        results = st.session_state.analysis_results['process']
        
        # Layout principal con dos columnas
        col_left, col_right = st.columns([1, 2])
        
        with col_left:
            # Representación del proceso
            #st.markdown("**Representación del proceso**")
            #st.write("**Métrica:** Recuento total")
            
            # Crear visualización usando modelo heurístico
            visualizer = ProcessVisualizer()
            
            try:
                with st.spinner("Generando modelo heurístico..."):
                    heuristic_result = visualizer.create_heuristic_net(st.session_state.event_log)
                    
                if heuristic_result and heuristic_result.get('success'):
                    # Mostrar la imagen del modelo heurístico
                    image_path = heuristic_result.get('image_path')
                    if image_path and os.path.exists(image_path):
                        st.image(image_path, use_container_width=True)
                        
                        # Mostrar métricas del modelo
                        #metrics = heuristic_result.get('metrics', {})
                        #if metrics:
                          #  col_metric1, col_metric2 = st.columns(2)
                          #  with col_metric1:
                               # st.write(f"**Fitness:** {metrics.get('Fitness', 'N/A')}")
                          #  with col_metric2:
                               # st.write(f"**Precision:** {metrics.get('Precision', 'N/A')}")
                    else:
                        st.info("Modelo heurístico generado correctamente")
                        st.write(f"**Actividades:** {results.get('num_activities', 0)}")
                        st.write(f"**Casos:** {results.get('num_cases', 0):,}")
                else:
                    # Mostrar error o información básica
                    error_msg = heuristic_result.get('error', 'Error desconocido') if heuristic_result else 'No se pudo generar el modelo'
                    st.warning(f"Problema generando modelo heurístico: {error_msg}")
                    st.write(f"**Actividades:** {results.get('num_activities', 0)}")
                    st.write(f"**Casos:** {results.get('num_cases', 0):,}")
                    
            except Exception as viz_error:
                st.error(f"Error generando modelo heurístico: {str(viz_error)}")
                st.write(f"**Actividades:** {results.get('num_activities', 0)}")
                st.write(f"**Casos:** {results.get('num_cases', 0):,}")
                st.info("Visualización detallada disponible en la sección 'Visualizaciones'")
        
        with col_right:
            # Métricas principales en grid 2x2
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric(
                    label="Recuento de casos",
                    value=f"{results.get('num_cases', 0):,}",
                    help="Número total de instancias de proceso"
                )
                
                st.metric(
                    label="Recuento de eventos", 
                    value=f"{results.get('num_events', 0):,}",
                    help="Número total de eventos ejecutados"
                )
            
            with col2:
                st.metric(
                    label="Recuento de variantes",
                    value=f"{len(results.get('variant_stats', [])):,}",
                    help="Número de variantes únicas del proceso"
                )
                
                st.metric(
                    label="Actividades",
                    value=f"{results.get('num_activities', 0):,}",
                    help="Número de actividades diferentes"
                )
        
        # Sección de variantes principales
        st.markdown("**10 variantes principales**")
        
        variant_stats = results.get('variant_stats', [])
        top_variants = variant_stats[:10]  # Top 10
        
        if top_variants:
            # Crear gráfico de barras horizontales para variantes
            variant_names = [f"Variant {i+1}" for i in range(len(top_variants))]
            variant_counts = [v['Count'] for v in top_variants]
            
            fig_variants = go.Figure(data=[
                go.Bar(
                    y=variant_names[::-1],  # Invertir para mostrar de mayor a menor
                    x=variant_counts[::-1],
                    orientation='h',
                    marker_color='#2E8B57',
                    text=variant_counts[::-1],
                    textposition='outside'
                )
            ])
            
            fig_variants.update_layout(
                height=400,
                showlegend=False,
                margin=dict(l=100, r=50, t=20, b=20),
                xaxis_title="Frecuencia",
                yaxis_title=""
            )
            
            st.plotly_chart(fig_variants, use_container_width=True)
        else:
            st.info("No hay datos de variantes disponibles")
        
        # Obtener análisis de transiciones y actividades
        transitions_data = get_process_transitions(st.session_state.event_log)
        activities_data = get_activity_frequency(st.session_state.event_log)
        
        # Layout para gráficos inferiores
        col_left_bottom, col_right_bottom = st.columns(2)
        
        with col_left_bottom:
            # Gráfico de transiciones principales
            st.markdown("**5 transiciones principales**")
            
            if transitions_data:
                # Tomar las top 5 transiciones
                top_transitions = transitions_data[:5]
                labels = [t['transition'] for t in top_transitions]
                values = [t['count'] for t in top_transitions]
                
                fig_transitions = px.pie(
                    values=values,
                    names=labels,
                    color_discrete_sequence=['#4472C4', '#E15759', '#70AD47', '#FFC000', '#9467BD'],
                    hole=0.5
                )
                
                # Agregar texto central
                total_transitions = sum(values)
                fig_transitions.add_annotation(
                    text=f"{total_transitions:,}",
                    x=0.5, y=0.5,
                    font_size=20,
                    showarrow=False
                )
                
                fig_transitions.update_traces(textinfo='percent')
                fig_transitions.update_layout(
                    height=300,
                    showlegend=True,
                    legend=dict(orientation="h", yanchor="top", y=-0.1)
                )
                
                st.plotly_chart(fig_transitions, use_container_width=True)
        
        with col_right_bottom:
            # Gráfico de actividades principales
            st.markdown("**10 actividades principales**")
            
            if activities_data:
                # Tomar las top 10 actividades
                top_activities = activities_data[:10]
                activity_names = [a['activity'] for a in top_activities]
                activity_counts = [a['count'] for a in top_activities]
                
                # Truncar nombres largos para mejor visualización
                short_names = [name[:15] + '...' if len(name) > 15 else name for name in activity_names]
                
                fig_activities = go.Figure(data=[
                    go.Bar(
                        x=short_names,
                        y=activity_counts,
                        marker_color='#4472C4',
                        text=activity_counts,
                        textposition='outside'
                    )
                ])
                
                fig_activities.update_layout(
                    height=300,
                    showlegend=False,
                    xaxis_title="Actividades",
                    yaxis_title="Recuento de casos",
                    xaxis_tickangle=-45,
                    margin=dict(l=50, r=50, t=20, b=100)
                )
                
                st.plotly_chart(fig_activities, use_container_width=True)
                
                # Leyenda personalizada
                #st.markdown("🔴 **Duración media** 🔵 **Recuento de casos**")
    
    except Exception as e:
        st.error(f"Error generando visión preliminar: {str(e)}")
        st.code(traceback.format_exc())

def get_process_transitions(event_log):
    """Obtener las transiciones más frecuentes del proceso"""
    try:
        transitions = {}
        
        for trace in event_log:
            activities = []
            for event in trace:
                if 'concept:name' in event:
                    activities.append(event['concept:name'])
            
            # Crear transiciones secuenciales
            for i in range(len(activities) - 1):
                transition = f"{activities[i]} -> {activities[i+1]}"
                transitions[transition] = transitions.get(transition, 0) + 1
        
        # Convertir a lista ordenada
        transition_list = [
            {'transition': trans, 'count': count}
            for trans, count in sorted(transitions.items(), key=lambda x: x[1], reverse=True)
        ]
        
        return transition_list
        
    except Exception as e:
        print(f"Error obteniendo transiciones: {str(e)}")
        return []

def get_activity_frequency(event_log):
    """Obtener la frecuencia de actividades"""
    try:
        activities = {}
        
        for trace in event_log:
            for event in trace:
                if 'concept:name' in event:
                    activity = event['concept:name']
                    activities[activity] = activities.get(activity, 0) + 1
        
        # Convertir a lista ordenada
        activity_list = [
            {'activity': activity, 'count': count}
            for activity, count in sorted(activities.items(), key=lambda x: x[1], reverse=True)
        ]
        
        return activity_list
        
    except Exception as e:
        print(f"Error obteniendo frecuencia de actividades: {str(e)}")
        return []

def show_visualizations():
    st.subheader("**📊 Visualizaciones del Proceso**")
    
    if st.session_state.event_log is None:
        st.warning("Primero debe cargar y mapear los datos")
        return
    
    visualizer = ProcessVisualizer()
    
    # Selector de tipo de visualización
    viz_type = st.selectbox(
        "Seleccionar tipo de visualización:",
        ["Red de Petri", "Algoritmo Heurístico", "Process Tree", "BPMN", "Grafos Dirigidos (DFG)"]
    )
    
    try:
        viz_data = None
        with st.spinner(f"Generando visualización: {viz_type}..."):
            if viz_type == "Red de Petri":
                viz_data = visualizer.create_petri_net(st.session_state.event_log)
            elif viz_type == "Algoritmo Heurístico":
                viz_data = visualizer.create_heuristic_net(st.session_state.event_log)
            elif viz_type == "Process Tree":
                viz_data = visualizer.create_process_tree(st.session_state.event_log)
            elif viz_type == "BPMN":
                viz_data = visualizer.create_bpmn(st.session_state.event_log)
            elif viz_type == "Grafos Dirigidos (DFG)":
                viz_data = visualizer.create_dfg(st.session_state.event_log)
        
        if viz_data and viz_data.get('success'):
            st.success(f"Visualización {viz_type} generada exitosamente")
            
            # Mostrar imagen
            if 'image_path' in viz_data:
                st.image(viz_data['image_path'], caption=f"Visualización: {viz_type}")
            
            # Mostrar métricas si están disponibles
            if 'metrics' in viz_data:
                st.subheader("Métricas del Modelo")
                metrics = viz_data['metrics']
                cols = st.columns(len(metrics))
                for i, (metric, value) in enumerate(metrics.items()):
                    with cols[i]:
                        st.metric(metric, value)
            
            # Guardar en session state para exportar
            st.session_state.analysis_results[f'viz_{viz_type.lower().replace(" ", "_")}'] = viz_data
            
        else:
            st.error(f"Error al generar la visualización {viz_type}")
            if viz_data and 'error' in viz_data:
                st.error(viz_data['error'])
                
    except Exception as e:
        st.error(f"Error al crear la visualización: {str(e)}")
        st.code(traceback.format_exc())

def show_ai_analysis():
    st.subheader("**🤖 Análisis con Inteligencia Artificial**")
    
    if st.session_state.event_log is None:
        st.warning("Primero debe cargar y mapear los datos")
        return
    
    # Verificar API key de OpenAI
    #api_key = os.getenv("OPENAI_API_KEY")
    openai_key = "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"
    api_key = openai_key  # Reemplazar con tu clave de API real

    if not api_key:
        st.error("No se ha configurado la API key de OpenAI. Configure la variable de entorno OPENAI_API_KEY.")
        return
    
    ai_analyzer = AIAnalyzer()
    
    # Opciones de análisis con IA
    analysis_type = st.selectbox(
        "Tipo de análisis con IA:",
        ["Análisis General del Proceso", "Identificación de Cuellos de Botella", 
         "Recomendaciones de Optimización", "Análisis de Anomalías"]
    )
    
    # Mostrar información sobre datos disponibles para IA
    with st.expander("📊 Información enviada a la IA"):
        available_analyses = []
        if 'process' in st.session_state.analysis_results:
            available_analyses.append("✅ Análisis de proceso básico")
        if 'variants' in st.session_state.analysis_results:
            available_analyses.append("✅ Análisis de variantes")
        if 'performance' in st.session_state.analysis_results:
            available_analyses.append("✅ Métricas de performance")
        if 'resources' in st.session_state.analysis_results:
            available_analyses.append("✅ Información de recursos")
        if 'costs' in st.session_state.analysis_results:
            available_analyses.append("✅ Información de costos")
        
        if available_analyses:
            st.write("**Datos que se enviarán a la IA:**")
            for analysis in available_analyses:
                st.write(analysis)
        else:
            st.warning("⚠️ Se recomienda realizar otros análisis primero para obtener mejores resultados de IA")
    
    # Botón para mostrar vista previa del prompt
    if st.button("👁️ Mostrar vista previa del prompt", type="secondary"):
        # Preparar datos para IA
        process_summary = ai_analyzer.prepare_process_summary(
            st.session_state.event_log,
            st.session_state.analysis_results
        )
        
        # Mostrar vista previa del prompt
        st.subheader("🔍 Vista previa del prompt que se enviará a la IA")
        
        with st.expander("📊 Resumen de datos del proceso", expanded=True):
            st.json(process_summary)
        
        # Generar el prompt que se enviará según el tipo de análisis
        preview_prompt = "Prompt no definido para este tipo de análisis"
        
        if analysis_type == "Análisis General del Proceso":
            preview_prompt = f"""Analiza el siguiente proceso de negocio y proporciona insights detallados en español.

Datos del proceso:
{json.dumps(process_summary, indent=2)}

Proporciona un análisis completo que incluya:
1. Resumen ejecutivo del proceso
2. Insights clave sobre eficiencia y rendimiento
3. Patrones identificados en el flujo del proceso
4. Áreas de oportunidad detectadas
5. Recomendaciones generales para mejoras

Responde en formato JSON con las siguientes claves:
- "executive_summary": resumen ejecutivo del proceso
- "key_insights": lista de insights principales
- "process_patterns": patrones identificados
- "opportunity_areas": áreas de oportunidad
- "general_recommendations": recomendaciones generales"""
        elif analysis_type == "Identificación de Cuellos de Botella":
            preview_prompt = f"""Analiza el siguiente proceso de negocio para identificar cuellos de botella y problemas de rendimiento.

Datos del proceso:
{json.dumps(process_summary, indent=2)}

Identifica:
1. Posibles cuellos de botella en el proceso
2. Actividades que consumen más tiempo
3. Recursos sobrecargados
4. Variantes problemáticas del proceso
5. Recomendaciones específicas para mejorar el rendimiento

Responde en formato JSON con las siguientes claves:
- "bottlenecks": lista de cuellos de botella identificados
- "time_consuming_activities": actividades que consumen más tiempo
- "overloaded_resources": recursos sobrecargados
- "problematic_variants": variantes problemáticas
- "performance_recommendations": recomendaciones para mejorar rendimiento"""
        elif analysis_type == "Recomendaciones de Optimización":
            preview_prompt = f"""Basándote en el análisis del siguiente proceso de negocio, proporciona recomendaciones específicas de optimización.

Datos del proceso:
{json.dumps(process_summary, indent=2)}

Proporciona recomendaciones para:
1. Reducir tiempos de ciclo
2. Mejorar la eficiencia de recursos
3. Reducir costos operativos
4. Estandarizar variantes del proceso
5. Implementar automatización
6. Mejorar la calidad del proceso

Responde en formato JSON con las siguientes claves:
- "cycle_time_reduction": recomendaciones para reducir tiempos
- "resource_efficiency": mejoras en eficiencia de recursos
- "cost_reduction": estrategias de reducción de costos
- "process_standardization": estandarización de procesos
- "automation_opportunities": oportunidades de automatización
- "quality_improvements": mejoras en calidad
- "priority_actions": acciones prioritarias"""
        elif analysis_type == "Análisis de Anomalías":
            preview_prompt = f"""Analiza el siguiente proceso de negocio para identificar anomalías y comportamientos atípicos.

Datos del proceso:
{json.dumps(process_summary, indent=2)}

Identifica:
1. Casos con comportamientos anómalos
2. Patrones de desviación en el proceso
3. Actividades con tiempos inusuales
4. Recursos con comportamiento atípico
5. Variantes que se desvían del flujo normal

Responde en formato JSON con las siguientes claves:
- "anomalous_cases": casos con comportamientos anómalos
- "deviation_patterns": patrones de desviación
- "unusual_activity_times": actividades con tiempos inusuales
- "atypical_resources": recursos con comportamiento atípico
- "unusual_variants": variantes que se desvían del flujo normal
- "anomaly_recommendations": recomendaciones para tratar las anomalías"""
        
        st.subheader("📝 Prompt completo:")
        st.text_area("Prompt:", value=preview_prompt.replace(" ", ""), height=400, disabled=False)
        
        # Información adicional
        st.info("💡 **Nota:** Este es exactamente el prompt que se enviará a OpenAI GPT-4o cuando hagas clic en 'Realizar Análisis con IA'")

    if st.button("Realizar Análisis con IA", type="primary"):
        try:
            result = None
            with st.spinner("Analizando con IA..."):
                # Preparar datos para IA
                process_summary = ai_analyzer.prepare_process_summary(
                    st.session_state.event_log,
                    st.session_state.analysis_results
                )
                
                if analysis_type == "Análisis General del Proceso":
                    result = ai_analyzer.general_process_analysis(process_summary)
                elif analysis_type == "Identificación de Cuellos de Botella":
                    result = ai_analyzer.bottleneck_analysis(process_summary)
                elif analysis_type == "Recomendaciones de Optimización":
                    result = ai_analyzer.optimization_recommendations(process_summary)
                elif analysis_type == "Análisis de Anomalías":
                    result = ai_analyzer.anomaly_analysis(process_summary)
            
            if result and result.get('success'):
                st.success("Análisis con IA completado")
                
                # Mostrar resultados
                if 'insights' in result:
                    st.subheader("Insights del Análisis")
                    for insight in result['insights']:
                        st.markdown(f"• {insight}")
                
                if 'recommendations' in result:
                    st.subheader("Recomendaciones")
                    for rec in result['recommendations']:
                        st.markdown(f"• {rec}")
                
                if 'detailed_analysis' in result:
                    st.subheader("Análisis Detallado")
                    st.markdown(result['detailed_analysis'])
                
                # Guardar resultados
                st.session_state.analysis_results[f'ai_{analysis_type.lower().replace(" ", "_")}'] = result
                
            else:
                st.error("Error en el análisis con IA")
                if result and 'error' in result:
                    st.error(result['error'])
                    
        except Exception as e:
            st.error(f"Error en el análisis con IA: {str(e)}")
            st.code(traceback.format_exc())

def show_export_results():
    st.header("📤 Exportar Resultados")
    
    if not st.session_state.analysis_results:
        st.warning("No hay resultados de análisis para exportar. Realice algunos análisis primero.")
        return
    
    exporter = ResultExporter()
    
    # Opciones de exportación
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Seleccionar Resultados")
        export_options = {}
        
        if 'process' in st.session_state.analysis_results:
            export_options['process'] = st.checkbox("Análisis de Proceso", value=True)
        if 'variants' in st.session_state.analysis_results:
            export_options['variants'] = st.checkbox("Análisis de Variantes", value=True)
        if 'costs' in st.session_state.analysis_results:
            export_options['costs'] = st.checkbox("Análisis de Costos", value=True)
        if 'resources' in st.session_state.analysis_results:
            export_options['resources'] = st.checkbox("Análisis de Recursos", value=True)
        
        # Visualizaciones
        viz_keys = [k for k in st.session_state.analysis_results.keys() if k.startswith('viz_')]
        for viz_key in viz_keys:
            export_options[viz_key] = st.checkbox(f"Visualización: {viz_key.replace('viz_', '').replace('_', ' ').title()}", value=True)
        
        # Análisis con IA
        ai_keys = [k for k in st.session_state.analysis_results.keys() if k.startswith('ai_')]
        for ai_key in ai_keys:
            export_options[ai_key] = st.checkbox(f"IA: {ai_key.replace('ai_', '').replace('_', ' ').title()}", value=True)
    
    with col2:
        st.subheader("Formato de Exportación")
        export_format = st.selectbox(
            "Seleccionar formato:",
            ["PDF", "Excel", "CSV", "JSON"]
        )
        
        include_visualizations = st.checkbox("Incluir visualizaciones", value=True)
        include_raw_data = st.checkbox("Incluir datos originales", value=False)
    
    if st.button("Generar Exportación", type="primary"):
        try:
            with st.spinner("Generando archivo de exportación..."):
                # Filtrar resultados seleccionados
                selected_results = {
                    k: v for k, v in st.session_state.analysis_results.items() 
                    if export_options.get(k, False)
                }
                
                if not selected_results:
                    st.warning("Seleccione al menos un resultado para exportar")
                    return
                
                # Generar exportación
                export_data = {
                    'results': selected_results,
                    'metadata': {
                        'export_date': datetime.now().isoformat(),
                        'format': export_format,
                        'include_visualizations': include_visualizations,
                        'include_raw_data': include_raw_data
                    }
                }
                
                # Incluir visualizaciones si están seleccionadas
                if include_visualizations:
                    for key in selected_results.keys():
                        if key.startswith('viz_'):
                            # Las visualizaciones ya están en selected_results
                            pass
                
                if include_raw_data and st.session_state.mapped_data is not None:
                    export_data['raw_data'] = st.session_state.mapped_data.to_dict()
                
                # Crear archivo
                file_data = None
                file_name = ""
                mime_type = ""
                
                if export_format == "PDF":
                    file_data = exporter.export_to_pdf(export_data)
                    file_name = f"analisis_procesos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                    mime_type = "application/pdf"
                elif export_format == "Excel":
                    file_data = exporter.export_to_excel(export_data)
                    file_name = f"analisis_procesos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                    mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                elif export_format == "CSV":
                    file_data = exporter.export_to_csv(export_data)
                    file_name = f"analisis_procesos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                    mime_type = "text/csv"
                elif export_format == "JSON":
                    file_data = exporter.export_to_json(export_data)
                    file_name = f"analisis_procesos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    mime_type = "application/json"
                
                # Mostrar botón de descarga solo si se generó el archivo
                if file_data:
                    st.download_button(
                        label=f"Descargar {export_format}",
                        data=file_data,
                        file_name=file_name,
                        mime=mime_type
                    )
                else:
                    st.error("Error generando el archivo de exportación")
                
                st.success(f"Archivo {export_format} generado exitosamente")
                
        except Exception as e:
            st.error(f"Error al generar la exportación: {str(e)}")
            st.code(traceback.format_exc())

  


if __name__ == "__main__":
    main()
