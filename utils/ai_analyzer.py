import json
import os
import pandas as pd
from openai import OpenAI

class AIAnalyzer:
    """Clase para análisis de procesos usando IA con OpenAI"""
    
    def __init__(self):
        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # do not change this unless explicitly requested by the user
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))
        self.model = "gpt-4o"
    
    def prepare_process_summary(self, event_log, analysis_results):
        """Preparar resumen del proceso para análisis con IA"""
        try:
            summary = {
                "process_statistics": {},
                "variants_info": {},
                "performance_metrics": {},
                "resource_info": {},
                "cost_info": {}
            }
            
            # Estadísticas básicas del proceso
            if 'process' in analysis_results:
                process_data = analysis_results['process']
                summary["process_statistics"] = {
                    "total_cases": process_data.get('num_cases', 0),
                    "total_events": process_data.get('num_events', 0),
                    "total_activities": process_data.get('num_activities', 0),
                    "avg_case_duration_days": process_data.get('avg_case_duration', 0),
                    "min_case_duration_days": process_data.get('min_case_duration', 0),
                    "max_case_duration_days": process_data.get('max_case_duration', 0),
                    "top_activities": process_data.get('activity_frequency', [])[:5]
                }
            
            # Información de variantes
            if 'variants' in analysis_results:
                variants_data = analysis_results['variants']
                summary["variants_info"] = {
                    "total_variants": variants_data.get('num_variants', 0),
                    "unique_variants": variants_data.get('unique_variants_count', 0),
                    "unique_variants_percentage": variants_data.get('unique_variants_percentage', 0),
                    "top_variants": variants_data.get('top_variants', [])[:3]
                }
            
            # Métricas de performance
            if 'performance' in analysis_results:
                performance_data = analysis_results['performance']
                
                # Extraer datos de performance de duración
                duration_perf = performance_data.get('duration_performance', {})
                cost_perf = performance_data.get('cost_performance', {})
                sla_perf = performance_data.get('sla_performance', {})
                variant_comparison = performance_data.get('variant_duration_comparison', [])
                
                summary["performance_metrics"] = {
                    "duration_performance": {
                        "ideal_variant_duration": duration_perf.get('ideal_variant_duration', 0),
                        "avg_process_duration": duration_perf.get('avg_process_duration', 0),
                        "performance_ratio": duration_perf.get('performance_ratio', 0),
                        "performance_percentage": duration_perf.get('performance_percentage', 0),
                        "ideal_variant": duration_perf.get('ideal_variant', 'N/A')
                    },
                    "cost_performance": {
                        "ideal_variant_cost": cost_perf.get('ideal_variant_cost', 0) if cost_perf else 0,
                        "avg_process_cost": cost_perf.get('avg_process_cost', 0) if cost_perf else 0,
                        "performance_ratio": cost_perf.get('performance_ratio', 0) if cost_perf else 0,
                        "performance_percentage": cost_perf.get('performance_percentage', 0) if cost_perf else 0,
                        "ideal_cost_variant": cost_perf.get('ideal_cost_variant', 'N/A') if cost_perf else 'N/A'
                    },
                    "sla_compliance": {
                        "target_days": sla_perf.get('target_days', 0) if sla_perf else 0,
                        "cases_within_sla": sla_perf.get('cases_within_sla', 0) if sla_perf else 0,
                        "total_cases": sla_perf.get('total_cases', 0) if sla_perf else 0,
                        "compliance_percentage": sla_perf.get('compliance_percentage', 0) if sla_perf else 0
                    },
                    "variant_performance": variant_comparison[:5] if variant_comparison else []
                }
            
            # Información de recursos
            if 'resources' in analysis_results:
                resources_data = analysis_results['resources']
                summary["resource_info"] = {
                    "total_resources": resources_data.get('num_resources', 0),
                    "avg_activities_per_resource": resources_data.get('avg_activities_per_resource', 0),
                    "top_resources": resources_data.get('resource_workload', [])[:5],
                    "resource_efficiency": resources_data.get('resource_efficiency', [])[:5],
                    "avg_resource_utilization": resources_data.get('avg_resource_utilization', 0)
                }
            
            # Información de costos
            if 'costs' in analysis_results:
                costs_data = analysis_results['costs']
                summary["cost_info"] = {
                    "total_cost": costs_data.get('total_cost', 0),
                    "avg_cost_per_case": costs_data.get('avg_cost_per_case', 0),
                    "avg_cost_per_activity": costs_data.get('avg_cost_per_activity', 0),
                    "min_cost_per_case": costs_data.get('min_cost_per_case', 0),
                    "max_cost_per_case": costs_data.get('max_cost_per_case', 0),
                    "top_cost_activities": costs_data.get('cost_by_activity', [])[:5],
                    "cost_distribution": costs_data.get('cost_distribution', {}),
                    "cost_efficiency_metrics": costs_data.get('cost_efficiency', {})
                }
            
            # Agregar información adicional del event log si está disponible
            if event_log:
                # Estadísticas adicionales del event log
                total_traces = len(event_log)
                total_events = sum(len(trace) for trace in event_log)
                unique_activities = set()
                unique_resources = set()
                
                for trace in event_log:
                    for event in trace:
                        if 'concept:name' in event:
                            unique_activities.add(event['concept:name'])
                        if 'org:resource' in event and pd.notna(event['org:resource']):
                            unique_resources.add(str(event['org:resource']))
                
                summary["event_log_metrics"] = {
                    "total_traces": total_traces,
                    "total_events": total_events,
                    "unique_activities_count": len(unique_activities),
                    "unique_resources_count": len(unique_resources),
                    "avg_events_per_trace": total_events / max(total_traces, 1),
                    "activities_list": list(unique_activities)[:10],
                    "resources_list": list(unique_resources)[:10]
                }
            
            return summary
            
        except Exception as e:
            raise Exception(f"Error al preparar resumen para IA: {str(e)}")
    
    def general_process_analysis(self, process_summary):
        """Análisis general del proceso usando IA"""
        try:
            prompt = f"""
            Analiza el siguiente proceso de negocio y proporciona insights detallados en español.
            
            Datos del proceso:
            {json.dumps(process_summary, indent=2)}
            
            Proporciona un análisis que incluya:
            1. Resumen ejecutivo del proceso
            2. Principales hallazgos y patrones identificados
            3. Indicadores de eficiencia del proceso
            4. Áreas que requieren atención
            5. Recomendaciones iniciales
            
            Responde en formato texto con las siguientes claves:
            - "executive_summary": resumen ejecutivo
            - "key_findings": lista de hallazgos principales
            - "efficiency_indicators": indicadores de eficiencia
            - "attention_areas": áreas que necesitan atención
            - "initial_recommendations": recomendaciones iniciales
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Eres un experto en process mining y análisis de procesos de negocio. Proporciona análisis detallados y profesionales en español."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            
            return {
                'success': True,
                'insights': result.get('key_findings', []),
                'recommendations': result.get('initial_recommendations', []),
                'detailed_analysis': result.get('executive_summary', ''),
                'efficiency_indicators': result.get('efficiency_indicators', ''),
                'attention_areas': result.get('attention_areas', [])
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Error en análisis general con IA: {str(e)}"
            }
    
    def bottleneck_analysis(self, process_summary):
        """Identificación de cuellos de botella usando IA"""
        try:
            prompt = f"""
            Analiza el siguiente proceso de negocio para identificar cuellos de botella y problemas de rendimiento.
            
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
            - "performance_recommendations": recomendaciones para mejorar rendimiento
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Eres un experto en análisis de rendimiento de procesos y identificación de cuellos de botella. Proporciona análisis detallados en español."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            
            return {
                'success': True,
                'insights': result.get('bottlenecks', []),
                'recommendations': result.get('performance_recommendations', []),
                'detailed_analysis': f"Cuellos de botella identificados: {len(result.get('bottlenecks', []))}\nActividades problemáticas: {len(result.get('time_consuming_activities', []))}\nRecursos sobrecargados: {len(result.get('overloaded_resources', []))}",
                'time_consuming_activities': result.get('time_consuming_activities', []),
                'overloaded_resources': result.get('overloaded_resources', [])
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Error en análisis de cuellos de botella: {str(e)}"
            }
    
    def optimization_recommendations(self, process_summary):
        """Generar recomendaciones de optimización usando IA"""
        try:
            prompt = f"""
            Basándote en el análisis del siguiente proceso de negocio, proporciona recomendaciones específicas de optimización.
            
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
            - "priority_actions": acciones prioritarias
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Eres un consultor experto en optimización de procesos de negocio. Proporciona recomendaciones prácticas y específicas en español."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            
            all_recommendations = []
            for key, value in result.items():
                if isinstance(value, list):
                    all_recommendations.extend(value)
                elif isinstance(value, str):
                    all_recommendations.append(value)
            
            return {
                'success': True,
                'insights': result.get('priority_actions', []),
                'recommendations': all_recommendations,
                'optimizations': all_recommendations,  # Alias para exportación
                'improvements': result.get('cycle_time_reduction', []) + result.get('automation_opportunities', []),
                'detailed_analysis': f"Se han identificado {len(all_recommendations)} recomendaciones de optimización específicas para mejorar el proceso.",
                'cycle_time_improvements': result.get('cycle_time_reduction', []),
                'automation_opportunities': result.get('automation_opportunities', [])
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Error en recomendaciones de optimización: {str(e)}"
            }
    
    def anomaly_analysis(self, process_summary):
        """Análisis de anomalías en el proceso usando IA"""
        try:
            prompt = f"""
            Analiza el siguiente proceso de negocio para identificar anomalías y comportamientos atípicos.
            
            Datos del proceso:
            {json.dumps(process_summary, indent=2)}
            
            Identifica:
            1. Casos con duraciones anómalamente largas o cortas
            2. Variantes del proceso poco comunes o problemáticas
            3. Patrones de comportamiento inusuales en recursos
            4. Anomalías en costos o eficiencia
            5. Desviaciones del flujo normal del proceso
            6. Recomendaciones para investigar y corregir anomalías
            
            Responde en formato JSON con las siguientes claves:
            - "duration_anomalies": anomalías en duración
            - "variant_anomalies": variantes anómalas
            - "resource_anomalies": comportamientos anómalos de recursos
            - "cost_anomalies": anomalías en costos
            - "process_deviations": desviaciones del proceso
            - "investigation_recommendations": recomendaciones de investigación
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Eres un experto en detección de anomalías en procesos de negocio. Identifica patrones atípicos y proporciona análisis en español."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            
            all_anomalies = []
            for key, value in result.items():
                if key != 'investigation_recommendations' and isinstance(value, list):
                    all_anomalies.extend(value)
            
            return {
                'success': True,
                'insights': all_anomalies[:10],  # Top 10 anomalías
                'recommendations': result.get('investigation_recommendations', []),
                'detailed_analysis': f"Se han detectado {len(all_anomalies)} anomalías potenciales en el proceso que requieren investigación.",
                'duration_anomalies': result.get('duration_anomalies', []),
                'variant_anomalies': result.get('variant_anomalies', [])
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Error en análisis de anomalías: {str(e)}"
            }
    
    def generate_process_insights(self, process_summary, custom_question):
        """Generar insights personalizados basados en una pregunta específica"""
        try:
            prompt = f"""
            Basándote en el análisis del siguiente proceso de negocio, responde la siguiente pregunta específica:
            
            Pregunta: {custom_question}
            
            Datos del proceso:
            {json.dumps(process_summary, indent=2)}
            
            Proporciona una respuesta detallada y profesional en español que incluya insights específicos y recomendaciones relevantes.
            
            Responde en formato texto con las siguientes claves:
            - "answer": respuesta detallada a la pregunta
            - "relevant_insights": insights relevantes
            - "supporting_data": datos que apoyan la respuesta
            - "recommendations": recomendaciones específicas
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Eres un experto consultor en process mining. Responde preguntas específicas sobre procesos de negocio con análisis detallados en español."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            
            return {
                'success': True,
                'insights': result.get('relevant_insights', []),
                'recommendations': result.get('recommendations', []),
                'detailed_analysis': result.get('answer', ''),
                'supporting_data': result.get('supporting_data', [])
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Error en análisis personalizado: {str(e)}"
            }


