import pm4py
import pandas as pd
from datetime import datetime, timedelta
import numpy as np

class ProcessAnalyzer:
    """Clase para realizar análisis de process mining usando pm4py"""
    
    def __init__(self):
        pass
    
    def analyze_process(self, event_log):
        """Análisis general del proceso"""
        try:
            results = {}
            
            # Estadísticas básicas
            results['num_cases'] = len(event_log)
            results['num_events'] = sum(len(trace) for trace in event_log)
            
            # Obtener actividades únicas
            activities = set()
            for trace in event_log:
                for event in trace:
                    activities.add(event['concept:name'])
            results['num_activities'] = len(activities)
            
            # Duración de casos
            case_durations = []
            
            for trace in event_log:
                if len(trace) > 0:
                    timestamps = [event['time:timestamp'] for event in trace if 'time:timestamp' in event]
                    if timestamps:
                        if len(timestamps) > 1:
                            duration = (max(timestamps) - min(timestamps)).total_seconds() / (24 * 3600)  # días
                            case_durations.append(max(duration, 0.001))
                        else:
                            # Si solo hay un evento, buscar duración de actividad
                            for event in trace:
                                if 'activity:duration' in event and pd.notna(event['activity:duration']):
                                    duration = float(event['activity:duration']) / (24 * 3600)
                                    case_durations.append(max(duration, 0.001))
                                    break
                            else:
                                case_durations.append(0.001)  # duración mínima por defecto
            
            if case_durations:
                results['avg_case_duration'] = np.mean(case_durations)
                results['min_case_duration'] = np.min(case_durations)
                results['max_case_duration'] = np.max(case_durations)
                results['case_durations'] = case_durations
            else:
                results['avg_case_duration'] = 0
                results['min_case_duration'] = 0
                results['max_case_duration'] = 0
                results['case_durations'] = []
            
            # Frecuencia de actividades
            activity_counts = {}
            for trace in event_log:
                for event in trace:
                    activity = event['concept:name']
                    activity_counts[activity] = activity_counts.get(activity, 0) + 1
            
            activity_freq = [
                {'Activity': activity, 'Frequency': count} 
                for activity, count in activity_counts.items()
            ]
            
            # Ordenar por frecuencia
            activity_freq.sort(key=lambda x: x['Frequency'], reverse=True)
            results['activity_frequency'] = activity_freq[:10]  # Top 10
            
            # Tiempo entre actividades
            results['avg_activity_duration'] = self._calculate_avg_activity_duration(event_log)
            
            # Casos por período
            results['cases_by_period'] = self._analyze_cases_by_period(event_log)
            
            # Agregar análisis básico de variantes para visión preliminar
            try:
                variants = pm4py.get_variants(event_log)
                variant_freq = []
                total_cases = len(event_log)
                
                for variant, traces in variants.items():
                    variant_str = ' -> '.join(variant)
                    # traces puede ser una lista o un número, manejar ambos casos
                    count = len(traces) if isinstance(traces, list) else traces
                    variant_freq.append({
                        'Variant': variant_str,
                        'Count': count,
                        'Percentage': (count / total_cases) * 100 if total_cases > 0 else 0
                    })
                
                # Ordenar por número de casos
                variant_freq.sort(key=lambda x: x['Count'], reverse=True)
                results['variant_stats'] = variant_freq[:10]  # Top 10 para visión preliminar
                
            except Exception as e:
                print(f"Error obteniendo variantes básicas: {str(e)}")
                results['variant_stats'] = []
            
            return results
            
        except Exception as e:
            raise Exception(f"Error en análisis de proceso: {str(e)}")
    
    def analyze_variants(self, event_log):
        """Análisis de variantes del proceso"""
        try:
            results = {}
            
            # Obtener variantes
            variants = pm4py.get_variants(event_log)
            results['num_variants'] = len(variants)
            
            # Top variantes por frecuencia
            variant_freq = []
            total_cases = len(event_log)
            
            for variant, traces in variants.items():
                variant_str = ' -> '.join(variant)
                # traces puede ser una lista o un número, manejar ambos casos
                count = len(traces) if isinstance(traces, list) else traces
                variant_freq.append({
                    'Variant': variant_str,
                    'Cases': count,
                    'Percentage': (count / total_cases) * 100 if total_cases > 0 else 0
                })
            
            # Ordenar por número de casos
            variant_freq.sort(key=lambda x: x['Cases'], reverse=True)
            results['top_variants'] = variant_freq[:10]
            
            # Análisis de conformidad (casos que siguen el flujo más común)
            if variant_freq:
                most_common_variant = variant_freq[0]
                results['conformance'] = [{
                    'Most_Common_Variant': most_common_variant['Variant'],
                    'Cases_Following': most_common_variant['Cases'],
                    'Conformance_Rate': most_common_variant['Percentage']
                }]
            
            # Variantes únicas (que aparecen solo una vez)
            unique_variants = [v for v in variant_freq if v['Cases'] == 1]
            results['unique_variants_count'] = len(unique_variants)
            results['unique_variants_percentage'] = (len(unique_variants) / len(variant_freq)) * 100 if variant_freq else 0
            
            return results
            
        except Exception as e:
            raise Exception(f"Error en análisis de variantes: {str(e)}")
    
    def analyze_costs(self, event_log):
        """Análisis de costos del proceso"""
        try:
            results = {}
            
            # Verificar si hay datos de costo
            has_cost_data = any(
                'cost:total' in event for trace in event_log for event in trace
            )
            
            if not has_cost_data:
                return None
            
            # Calcular costos totales
            total_cost = 0
            costs_by_activity = {}
            costs_by_case = {}
            
            for trace in event_log:
                case_id = trace.attributes['concept:name']
                case_cost = 0
                
                for event in trace:
                    if 'cost:total' in event and pd.notna(event['cost:total']):
                        cost = float(event['cost:total'])
                        activity = event['concept:name']
                        
                        total_cost += cost
                        case_cost += cost
                        
                        if activity not in costs_by_activity:
                            costs_by_activity[activity] = 0
                        costs_by_activity[activity] += cost
                
                if case_cost > 0:
                    costs_by_case[case_id] = case_cost
            
            results['total_cost'] = total_cost
            results['avg_cost_per_case'] = total_cost / len(costs_by_case) if costs_by_case else 0
            results['avg_cost_per_activity'] = total_cost / len(costs_by_activity) if costs_by_activity else 0
            
            # Costos por actividad
            cost_by_activity = [
                {'Activity': activity, 'Total_Cost': cost, 'Avg_Cost': cost / sum(1 for trace in event_log for event in trace if event['concept:name'] == activity)}
                for activity, cost in costs_by_activity.items()
            ]
            cost_by_activity.sort(key=lambda x: x['Total_Cost'], reverse=True)
            results['cost_by_activity'] = cost_by_activity
            
            # Costos por caso
            case_costs = list(costs_by_case.values())
            if case_costs:
                results['min_case_cost'] = min(case_costs)
                results['max_case_cost'] = max(case_costs)
                results['median_case_cost'] = np.median(case_costs)
            
            return results
            
        except Exception as e:
            raise Exception(f"Error en análisis de costos: {str(e)}")
    
    def analyze_resources(self, event_log):
        """Análisis de recursos del proceso"""
        try:
            results = {}
            
            # Verificar si hay datos de recursos
            has_resource_data = any(
                'org:resource' in event for trace in event_log for event in trace
            )
            
            if not has_resource_data:
                return None
            
            # Obtener recursos únicos
            resources = set()
            resource_activities = {}
            resource_cases = {}
            
            for trace in event_log:
                case_id = trace.attributes['concept:name']
                
                for event in trace:
                    if 'org:resource' in event and pd.notna(event['org:resource']):
                        resource = str(event['org:resource'])
                        activity = event['concept:name']
                        
                        resources.add(resource)
                        
                        if resource not in resource_activities:
                            resource_activities[resource] = set()
                            resource_cases[resource] = set()
                        
                        resource_activities[resource].add(activity)
                        resource_cases[resource].add(case_id)
            
            results['num_resources'] = len(resources)
            
            # Carga de trabajo por recurso
            resource_workload = []
            for resource in resources:
                activities_count = len(resource_activities.get(resource, set()))
                cases_count = len(resource_cases.get(resource, set()))
                
                resource_workload.append({
                    'Resource': resource,
                    'Activities': activities_count,
                    'Cases': cases_count
                })
            
            resource_workload.sort(key=lambda x: x['Activities'], reverse=True)
            results['resource_workload'] = resource_workload
            
            # Promedio de actividades por recurso
            if resource_workload:
                avg_activities = sum(r['Activities'] for r in resource_workload) / len(resource_workload)
                results['avg_activities_per_resource'] = avg_activities
            
            # Matriz recurso-actividad
            all_activities = set(event['concept:name'] for trace in event_log for event in trace)
            matrix_data = []
            
            for resource in list(resources)[:10]:  # Limitar a top 10 recursos
                row = {'Resource': resource}
                for activity in list(all_activities)[:10]:  # Limitar a top 10 actividades
                    count = sum(1 for trace in event_log for event in trace 
                              if event.get('org:resource') == resource and event['concept:name'] == activity)
                    row[activity] = count
                matrix_data.append(row)
            
            results['resource_activity_matrix'] = matrix_data
            
            return results
            
        except Exception as e:
            raise Exception(f"Error en análisis de recursos: {str(e)}")
    
    def analyze_performance(self, event_log, sla_target_days=None):
        """Análisis de performance del proceso"""
        try:
            results = {}
            
            # Obtener duraciones por caso y variante
            case_durations = {}
            variant_durations = {}
            case_variants = {}
            
            # Obtener variantes
            variants = pm4py.get_variants(event_log)
            
            for trace in event_log:
                case_id = trace.attributes.get('concept:name', 'Unknown')
                
                if len(trace) > 0:
                    try:
                        timestamps = []
                        activities = []
                        
                        for event in trace:
                            if 'time:timestamp' in event:
                                timestamps.append(event['time:timestamp'])
                            if 'concept:name' in event:
                                activities.append(event['concept:name'])
                        
                        if timestamps:
                            # Calcular duración del caso completo usando el rango de timestamps
                            calculated_duration = 0.001  # valor por defecto
                            
                            if len(timestamps) > 1:
                                calculated_duration = (max(timestamps) - min(timestamps)).total_seconds() / (24 * 3600)  # días
                                calculated_duration = max(calculated_duration, 0.001)  # Evitar duraciones de 0
                            else:
                                # Si solo hay un evento, usar duración de actividad si está disponible
                                for event in trace:
                                    if 'activity:duration' in event and pd.notna(event['activity:duration']):
                                        calculated_duration = float(event['activity:duration']) / (24 * 3600)  # convertir a días
                                        calculated_duration = max(calculated_duration, 0.001)
                                        break
                            
                            case_durations[case_id] = calculated_duration
                            
                            # Determinar la variante de este caso (solo actividades únicas)
                            unique_activities = []
                            seen = set()
                            for activity in activities:
                                if activity not in seen:
                                    unique_activities.append(activity)
                                    seen.add(activity)
                            
                            case_activities = tuple(unique_activities)
                            case_variants[case_id] = case_activities
                            
                            if case_activities not in variant_durations:
                                variant_durations[case_activities] = []
                            variant_durations[case_activities].append(calculated_duration)
                            
                    except Exception as e:
                        print(f"Error procesando caso {case_id}: {str(e)}")
                        continue
            
            # Validar que tenemos datos válidos
            if not case_durations:
                raise Exception("No se pudieron calcular duraciones válidas de los casos")
            
            # Calcular duración promedio del proceso
            valid_durations = [d for d in case_durations.values() if d > 0 and not np.isnan(d)]
            if not valid_durations:
                raise Exception("No se encontraron duraciones válidas para analizar")
                
            avg_process_duration = np.mean(valid_durations)
            
            # Encontrar variante ideal (menor duración promedio)
            variant_avg_durations = {}
            for variant, durations in variant_durations.items():
                valid_variant_durations = [d for d in durations if d > 0 and not np.isnan(d)]
                if valid_variant_durations:
                    variant_avg_durations[variant] = np.mean(valid_variant_durations)
            
            if not variant_avg_durations:
                raise Exception("No se encontraron variantes válidas para analizar")
                
            ideal_variant = min(variant_avg_durations.items(), key=lambda x: x[1])
            ideal_duration = ideal_variant[1]
            
            # Calcular desempeño por duración (variante ideal / promedio proceso)
            duration_performance_ratio = (ideal_duration / avg_process_duration) if avg_process_duration > 0 else 0
            
            results['duration_performance'] = {
                'ideal_variant_duration': ideal_duration,
                'avg_process_duration': avg_process_duration,
                'performance_ratio': duration_performance_ratio,
                'performance_percentage': duration_performance_ratio * 100,
                'ideal_variant': ' -> '.join(ideal_variant[0]) if ideal_variant else 'N/A'
            }
            
            # Análisis de costos si están disponibles
            has_cost_data = any('cost:total' in event for trace in event_log for event in trace)
            
            if has_cost_data:
                case_costs = {}
                variant_costs = {}
                
                for trace in event_log:
                    case_id = trace.attributes.get('concept:name', 'Unknown')
                    case_cost = 0
                    
                    try:
                        for event in trace:
                            if 'cost:total' in event and pd.notna(event['cost:total']):
                                try:
                                    cost_value = float(event['cost:total'])
                                    if cost_value > 0:
                                        case_cost += cost_value
                                except (ValueError, TypeError):
                                    continue
                        
                        if case_cost > 0:
                            case_costs[case_id] = case_cost
                            variant = case_variants.get(case_id)
                            if variant:
                                if variant not in variant_costs:
                                    variant_costs[variant] = []
                                variant_costs[variant].append(case_cost)
                                
                    except Exception as e:
                        print(f"Error procesando costos para caso {case_id}: {str(e)}")
                        continue
                
                avg_process_cost = np.mean(list(case_costs.values())) if case_costs else 0
                
                # Encontrar variante ideal por costo
                variant_avg_costs = {}
                for variant, costs in variant_costs.items():
                    variant_avg_costs[variant] = np.mean(costs)
                
                ideal_cost_variant = min(variant_avg_costs.items(), key=lambda x: x[1]) if variant_avg_costs else None
                ideal_cost = ideal_cost_variant[1] if ideal_cost_variant else 0
                
                # Calcular desempeño por costo (costo variante ideal / costo promedio proceso)
                cost_performance_ratio = (ideal_cost / avg_process_cost) if avg_process_cost > 0 else 0
                
                results['cost_performance'] = {
                    'ideal_variant_cost': ideal_cost,
                    'avg_process_cost': avg_process_cost,
                    'performance_ratio': cost_performance_ratio,
                    'performance_percentage': cost_performance_ratio * 100,
                    'ideal_cost_variant': ' -> '.join(ideal_cost_variant[0]) if ideal_cost_variant else 'N/A'
                }
            else:
                results['cost_performance'] = None
            
            # Análisis de SLA si se proporciona target
            if sla_target_days:
                cases_within_sla = sum(1 for duration in case_durations.values() if duration <= sla_target_days)
                total_cases = len(case_durations)
                sla_compliance = (cases_within_sla / total_cases) * 100 if total_cases > 0 else 0
                
                results['sla_performance'] = {
                    'target_days': sla_target_days,
                    'cases_within_sla': cases_within_sla,
                    'total_cases': total_cases,
                    'compliance_percentage': sla_compliance,
                    'cases_over_sla': total_cases - cases_within_sla
                }
            else:
                results['sla_performance'] = None
            
            # Comparación de duración por variante
            variant_comparison = []
            for variant, durations in variant_durations.items():
                variant_str = ' -> '.join(variant)
                variant_comparison.append({
                    'Variante': variant_str,
                    'Casos': len(durations),
                    'Duración_Promedio': np.mean(durations),
                    'Duración_Mínima': np.min(durations),
                    'Duración_Máxima': np.max(durations),
                    'Desviación_Estándar': np.std(durations)
                })
            
            # Ordenar por duración promedio
            variant_comparison.sort(key=lambda x: x['Duración_Promedio'])
            results['variant_duration_comparison'] = variant_comparison
            
            return results
            
        except Exception as e:
            raise Exception(f"Error en análisis de performance: {str(e)}")
    
    def _calculate_avg_activity_duration(self, event_log):
        """Calcular duración promedio de actividades"""
        try:
            durations = []
            
            for trace in event_log:
                events_by_activity = {}
                
                for event in trace:
                    activity = event['concept:name']
                    lifecycle = event.get('lifecycle:transition', 'complete')
                    timestamp = event['time:timestamp']
                    
                    if activity not in events_by_activity:
                        events_by_activity[activity] = {}
                    
                    events_by_activity[activity][lifecycle] = timestamp
                
                # Calcular duración para cada actividad
                for activity, events in events_by_activity.items():
                    if 'start' in events and 'complete' in events:
                        duration = (events['complete'] - events['start']).total_seconds() / 3600  # horas
                        durations.append(duration)
            
            return np.mean(durations) if durations else 0
            
        except Exception as e:
            return 0
    
    def _analyze_cases_by_period(self, event_log):
        """Analizar casos por período de tiempo"""
        try:
            cases_by_date = {}
            
            for trace in event_log:
                case_id = trace.attributes['concept:name']
                timestamps = [event['time:timestamp'] for event in trace]
                
                if timestamps:
                    case_start = min(timestamps).date()
                    if case_start not in cases_by_date:
                        cases_by_date[case_start] = 0
                    cases_by_date[case_start] += 1
            
            # Convertir a lista ordenada
            period_data = [
                {'Date': date.isoformat(), 'Cases': count}
                for date, count in sorted(cases_by_date.items())
            ]
            
            return period_data
            
        except Exception as e:
            return []
