import pm4py
import graphviz
import tempfile
import os
from datetime import datetime

class ProcessVisualizer:
    """Clase para crear visualizaciones de procesos usando pm4py y Graphviz"""
    
    def __init__(self):
        self.temp_dir = tempfile.gettempdir()
    
    def create_petri_net(self, event_log):
        """Crear visualización de Red de Petri"""
        try:
            # Descubrir Red de Petri usando algoritmo inductive miner
            petri_net, initial_marking, final_marking = pm4py.discover_petri_net_inductive(event_log)
            
            # Calcular métricas de fitness
            try:
                fitness = pm4py.fitness_token_based_replay(event_log, petri_net, initial_marking, final_marking)['log_fitness']
                precision = pm4py.precision_token_based_replay(event_log, petri_net, initial_marking, final_marking)
            except:
                fitness = 0.0
                precision = 0.0
            
            # Generar visualización
            filename = f"petri_net_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            file_path = os.path.join(self.temp_dir, f"{filename}.png")
            
            # Visualizar y guardar
            from pm4py.visualization.petri_net import visualizer as pn_visualizer
            gviz = pn_visualizer.apply(petri_net, initial_marking, final_marking)
            pn_visualizer.save(gviz, file_path)
            
            return {
                'success': True,
                'image_path': file_path,
                'metrics': {
                    'Fitness': f"{fitness:.3f}",
                    'Precision': f"{precision:.3f}",
                    'Places': len(petri_net.places),
                    'Transitions': len(petri_net.transitions)
                },
                'model': {
                    'petri_net': petri_net,
                    'initial_marking': initial_marking,
                    'final_marking': final_marking
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Error al crear Red de Petri: {str(e)}"
            }
    
    def create_heuristic_net(self, event_log):
        """Crear visualización usando algoritmo heurístico"""
        try:
            # Descubrir modelo usando heuristic miner
            heuristic_net = pm4py.discover_heuristics_net(event_log)
            
            # Convertir a Petri net para evaluación
            petri_net, initial_marking, final_marking = pm4py.convert_to_petri_net(heuristic_net)
            
            # Calcular métricas
            try:
                fitness = pm4py.fitness_token_based_replay(event_log, petri_net, initial_marking, final_marking)['log_fitness']
                precision = pm4py.precision_token_based_replay(event_log, petri_net, initial_marking, final_marking)
            except:
                fitness = 0.0
                precision = 0.0
            
            # Generar visualización
            filename = f"heuristic_net_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            file_path = os.path.join(self.temp_dir, f"{filename}.png")
            
            # Visualizar
            from pm4py.visualization.heuristics_net import visualizer as hn_visualizer
            gviz = hn_visualizer.apply(heuristic_net)
            hn_visualizer.save(gviz, file_path)
            
            return {
                'success': True,
                'image_path': file_path,
                'metrics': {
                    'Fitness': f"{fitness:.3f}",
                    'Precision': f"{precision:.3f}",
                    'Activities': len(heuristic_net.activities),
                    'Dependencies': len(heuristic_net.dependency_matrix)
                },
                'model': heuristic_net
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Error al crear red heurística: {str(e)}"
            }
    
    def create_process_tree(self, event_log):
        """Crear visualización de Process Tree"""
        try:
            # Descubrir process tree
            process_tree = pm4py.discover_process_tree_inductive(event_log)
            
            # Convertir a Petri net para evaluación
            petri_net, initial_marking, final_marking = pm4py.convert_to_petri_net(process_tree)
            
            # Calcular métricas
            try:
                fitness = pm4py.fitness_token_based_replay(event_log, petri_net, initial_marking, final_marking)['log_fitness']
                precision = pm4py.precision_token_based_replay(event_log, petri_net, initial_marking, final_marking)
            except:
                fitness = 0.0
                precision = 0.0
            
            # Generar visualización
            filename = f"process_tree_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            file_path = os.path.join(self.temp_dir, f"{filename}.png")
            
            # Crear visualización del process tree usando pm4py.view_process_tree
            try:
                # Usar la función específica recomendada
                gviz = pm4py.view_process_tree(process_tree)
                
                # Guardar en archivo temporal
                pm4py.save_vis_process_tree(gviz, file_path)
                
            except Exception as ex:
                # Si falla, usar visualización personalizada con el estilo exacto de la imagen
                dot = graphviz.Digraph(comment='Process Tree')
                dot.attr(rankdir='TB', size='12,8', dpi='300', bgcolor='white')
                dot.attr('node', fontname='Arial', fontsize='11', fontcolor='black')
                dot.attr('edge', color='black', arrowhead='normal', arrowsize='0.8')
                
                # Función recursiva para construir el árbol con estilo exacto
                def build_tree_visualization(tree, parent_id=None, dot=dot, node_counter=[0]):
                    if tree is None:
                        return None
                    
                    node_counter[0] += 1
                    current_id = f"node_{node_counter[0]}"
                    
                    # Determinar etiqueta y estilo del nodo (todos ovalados como en la imagen)
                    if hasattr(tree, 'label') and tree.label:
                        # Actividades - nodos ovalados
                        label = str(tree.label)
                        dot.node(current_id, label, shape='ellipse', 
                                style='filled', fillcolor='white', 
                                fontcolor='black', margin='0.1,0.05')
                    elif hasattr(tree, 'operator'):
                        # Operadores - nodos ovalados con nombres específicos
                        operator = str(tree.operator)
                        if operator == 'X' or operator == '×':
                            label = 'xor'
                        elif operator == '+':
                            label = 'or'
                        elif operator == '*':
                            label = 'xor loop'
                        elif operator == '→' or operator == 'SEQ':
                            label = 'seq'
                        elif operator == '∧' or operator == 'AND':
                            label = 'and'
                        else:
                            label = str(operator).lower()
                        
                        dot.node(current_id, label, shape='ellipse', 
                                style='filled', fillcolor='white',
                                fontcolor='black', margin='0.1,0.05')
                    else:
                        # Nodos silenciosos
                        dot.node(current_id, 'τ', shape='ellipse', 
                                style='filled', fillcolor='white',
                                fontcolor='black', margin='0.1,0.05')
                    
                    if parent_id:
                        dot.edge(parent_id, current_id)
                    
                    # Procesar hijos si existen
                    if hasattr(tree, 'children') and tree.children:
                        for child in tree.children:
                            build_tree_visualization(child, current_id, dot, node_counter)
                    
                    return current_id
                
                # Construir visualización
                build_tree_visualization(process_tree)
                
                # Renderizar con nombre temporal diferente
                temp_filename = f"process_tree_custom_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                temp_path = os.path.join(self.temp_dir, temp_filename)
                dot.render(temp_path, format='png', cleanup=True, quiet=True)
                file_path = f"{temp_path}.png"
                print(f"Custom process tree saved to {file_path}")
            
            # Contar nodos del árbol
            def count_nodes(tree):
                if tree is None:
                    return 0
                count = 1
                if hasattr(tree, 'children'):
                    for child in tree.children:
                        count += count_nodes(child)
                return count
            
            return {
                'success': True,
                'image_path': file_path,
                'metrics': {
                    'Fitness': f"{fitness:.3f}",
                    'Precision': f"{precision:.3f}",
                    'Tree_Nodes': count_nodes(process_tree),
                    'Tree_Depth': self._calculate_tree_depth(process_tree)
                },
                'model': process_tree
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Error al crear Process Tree: {str(e)}"
            }
    
    def create_bpmn(self, event_log):
        """Crear visualización BPMN"""
        try:
            # Descubrir process tree primero
            process_tree = pm4py.discover_process_tree_inductive(event_log)
            
            # Convertir a BPMN
            bpmn_diagram = pm4py.convert_to_bpmn(process_tree)
            
            # Convertir a Petri net para evaluación
            petri_net, initial_marking, final_marking = pm4py.convert_to_petri_net(process_tree)
            
            # Calcular métricas
            try:
                fitness = pm4py.fitness_token_based_replay(event_log, petri_net, initial_marking, final_marking)['log_fitness']
                precision = pm4py.precision_token_based_replay(event_log, petri_net, initial_marking, final_marking)
            except:
                fitness = 0.0
                precision = 0.0
            
            # Generar visualización
            filename = f"bpmn_diagram_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            file_path = os.path.join(self.temp_dir, f"{filename}.png")
            
            # Visualizar
            from pm4py.visualization.bpmn import visualizer as bpmn_visualizer
            gviz = bpmn_visualizer.apply(bpmn_diagram)
            bpmn_visualizer.save(gviz, file_path)
            
            return {
                'success': True,
                'image_path': file_path,
                'metrics': {
                    'Fitness': f"{fitness:.3f}",
                    'Precision': f"{precision:.3f}",
                    'BPMN_Elements': len(bpmn_diagram.get_nodes()),
                    'BPMN_Flows': len(bpmn_diagram.get_flows())
                },
                'model': bpmn_diagram
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Error al crear diagrama BPMN: {str(e)}"
            }
    
    def create_dfg(self, event_log):
        """Crear visualización de Grafo Dirigido de Frecuencias (DFG)"""
        try:
            # Descubrir DFG usando pm4py
            dfg, start_activities, end_activities = pm4py.discover_dfg(event_log)
            
            # Crear archivo temporal
            filename = f"dfg_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            file_path = os.path.join(self.temp_dir, filename)
            
            # Crear visualización DFG con fondo blanco
            dot = graphviz.Digraph(comment='DFG')
            dot.attr(bgcolor='white', size='12,8', dpi='300')
            dot.attr('node', fontname='Arial', fontsize='10', fontcolor='black')
            dot.attr('edge', color='black', arrowhead='normal', arrowsize='0.8')
            
            # Agregar nodo de inicio (círculo verde)
            dot.node('START', '', shape='circle', style='filled', 
                    fillcolor='#00FF00', width='0.8', height='0.8', fixedsize='true')
            
            # Agregar nodo de fin (círculo naranja)
            dot.node('END', '', shape='circle', style='filled', 
                    fillcolor='#FFA500', width='0.8', height='0.8', fixedsize='true')
            
            # Agregar todas las actividades del DFG como nodos rectangulares blancos
            activities = set()
            if dfg:
                for (source, target), frequency in dfg.items():
                    activities.add(source)
                    activities.add(target)
            
            for activity in activities:
                # Agregar frecuencia de la actividad si existe
                freq_text = ""
                if start_activities and activity in start_activities:
                    freq_text = f" ({start_activities[activity]})"
                elif end_activities and activity in end_activities:
                    freq_text = f" ({end_activities[activity]})"
                
                dot.node(activity, f"{activity}{freq_text}", 
                        shape='rectangle', style='filled', fillcolor='white',
                        fontcolor='black', margin='0.1,0.05')
            
            # Conectar START con actividades iniciales
            if start_activities:
                for activity in start_activities.keys():
                    dot.edge('START', activity, color='black')
            
            # Agregar arcos del DFG entre actividades
            if dfg:
                for (source, target), frequency in dfg.items():
                    dot.edge(source, target, color='black')
            
            # Conectar actividades finales con END
            if end_activities:
                for activity in end_activities.keys():
                    dot.edge(activity, 'END', color='black')
            
            # Renderizar el grafo
            dot.render(file_path, format='png', cleanup=True)
            final_path = f"{file_path}.png"
            
            # Calcular estadísticas del DFG
            total_edges = len(dfg) if dfg else 0
            total_frequency = sum(dfg.values()) if dfg else 0
            most_frequent_edge = max(dfg.items(), key=lambda x: x[1]) if dfg else None
            
            # Preparar métricas
            metrics = {
                "Total de Arcos": total_edges,
                "Frecuencia Total": int(total_frequency),
                "Actividades de Inicio": len(start_activities) if start_activities else 0,
                "Actividades de Fin": len(end_activities) if end_activities else 0,
                "Actividades Únicas": len(activities)
            }
            
            if most_frequent_edge:
                edge_from, edge_to = most_frequent_edge[0]
                frequency = most_frequent_edge[1]
                metrics["Arco Más Frecuente"] = f"{edge_from} → {edge_to} ({frequency})"
            
            return {
                'success': True,
                'image_path': final_path,
                'metrics': metrics,
                'dfg_data': {
                    'dfg': dict(dfg) if dfg else {},
                    'start_activities': dict(start_activities) if start_activities else {},
                    'end_activities': dict(end_activities) if end_activities else {},
                    'total_edges': total_edges,
                    'total_frequency': int(total_frequency)
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Error al crear DFG: {str(e)}"
            }
    
    def create_custom_graph(self, data, title="Process Graph"):
        """Crear gráfico personalizado usando Graphviz"""
        try:
            dot = graphviz.Digraph(comment=title)
            dot.attr(rankdir='LR', size='12,8', dpi='300')
            dot.attr('node', shape='rectangle', style='rounded,filled', fillcolor='lightblue')
            dot.attr('edge', color='gray', fontsize='10')
            
            # Agregar nodos y edges según los datos
            if 'nodes' in data:
                for node in data['nodes']:
                    dot.node(node['id'], node['label'])
            
            if 'edges' in data:
                for edge in data['edges']:
                    dot.edge(edge['from'], edge['to'], label=edge.get('label', ''))
            
            # Generar imagen
            filename = f"custom_graph_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            file_path = os.path.join(self.temp_dir, filename)
            
            dot.render(file_path, format='png', cleanup=True)
            
            return {
                'success': True,
                'image_path': f"{file_path}.png",
                'dot_source': dot.source
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Error al crear gráfico personalizado: {str(e)}"
            }
    
    def _calculate_tree_depth(self, tree, depth=0):
        """Calcular la profundidad de un process tree"""
        if tree is None:
            return depth
        
        max_child_depth = depth
        if hasattr(tree, 'children'):
            for child in tree.children:
                child_depth = self._calculate_tree_depth(child, depth + 1)
                max_child_depth = max(max_child_depth, child_depth)
        
        return max_child_depth
    
    def generate_summary_visualization(self, analysis_results):
        """Generar visualización resumen de todos los análisis"""
        try:
            dot = graphviz.Digraph(comment='Process Analysis Summary')
            dot.attr(rankdir='TB', size='16,12', dpi='300')
            dot.attr('node', shape='rectangle', style='rounded,filled')
            
            # Nodo principal
            dot.node('summary', 'Resumen del Proceso', fillcolor='lightgreen', fontsize='16')
            
            # Agregar métricas si están disponibles
            if 'process' in analysis_results:
                process_data = analysis_results['process']
                metrics_text = f"Casos: {process_data.get('num_cases', 'N/A')}\\n"
                metrics_text += f"Eventos: {process_data.get('num_events', 'N/A')}\\n"
                metrics_text += f"Actividades: {process_data.get('num_activities', 'N/A')}\\n"
                metrics_text += f"Duración Promedio: {process_data.get('avg_case_duration', 'N/A'):.2f} días"
                
                dot.node('metrics', metrics_text, fillcolor='lightblue')
                dot.edge('summary', 'metrics', label='Métricas Básicas')
            
            # Agregar información de variantes
            if 'variants' in analysis_results:
                variants_data = analysis_results['variants']
                variants_text = f"Total Variantes: {variants_data.get('num_variants', 'N/A')}\\n"
                variants_text += f"Variantes Únicas: {variants_data.get('unique_variants_count', 'N/A')}"
                
                dot.node('variants', variants_text, fillcolor='lightyellow')
                dot.edge('summary', 'variants', label='Variantes')
            
            # Generar imagen
            filename = f"summary_viz_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            file_path = os.path.join(self.temp_dir, filename)
            
            dot.render(file_path, format='png', cleanup=True)
            
            return {
                'success': True,
                'image_path': f"{file_path}.png",
                'dot_source': dot.source
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Error al crear visualización resumen: {str(e)}"
            }