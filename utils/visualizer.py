import pm4py
import tempfile
import os
import subprocess
import shutil
from datetime import datetime

try:
    import graphviz
    GRAPHVIZ_AVAILABLE = True
except ImportError:
    GRAPHVIZ_AVAILABLE = False

def check_graphviz_executable():
    """Verificar si el ejecutable de Graphviz está disponible"""
    return shutil.which('dot') is not None

class ProcessVisualizer:
    """Clase para crear visualizaciones de procesos usando pm4py y Graphviz"""
    
    def __init__(self):
        self.temp_dir = tempfile.gettempdir()
        self.graphviz_available = GRAPHVIZ_AVAILABLE and check_graphviz_executable()
    
    def create_petri_net(self, event_log):
        """Crear visualización de Red de Petri"""
        if not self.graphviz_available:
            return self._create_alternative_visualization(event_log, "petri_net")
        
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
    def _create_alternative_visualization(self, event_log, viz_type):
        """Crear visualización alternativa cuando Graphviz no está disponible"""
        try:
            import matplotlib.pyplot as plt
            import pandas as pd
            import networkx as nx
            from collections import defaultdict
            
            # Convertir event log a DataFrame si es necesario
            if hasattr(event_log, 'to_dict'):
                df = pd.DataFrame(event_log.to_dict())
            else:
                df = event_log
            
            # Crear grafo de flujo de proceso
            G = nx.DiGraph()
            transitions = defaultdict(int)
            
            # Agrupar por caso y crear secuencias
            for case_id in df['case:concept:name'].unique():
                case_events = df[df['case:concept:name'] == case_id].sort_values('time:timestamp')
                activities = case_events['concept:name'].tolist()
                
                # Agregar transiciones
                for i in range(len(activities) - 1):
                    from_activity = activities[i]
                    to_activity = activities[i + 1]
                    transitions[(from_activity, to_activity)] += 1
                    G.add_edge(from_activity, to_activity, weight=transitions[(from_activity, to_activity)])
            
            # Crear visualización con matplotlib
            plt.figure(figsize=(12, 8))
            plt.title(f'Flujo de Proceso - {viz_type.replace("_", " ").title()}')
            
            # Layout del grafo
            pos = nx.spring_layout(G, k=2, iterations=50)
            
            # Dibujar nodos
            nx.draw_networkx_nodes(G, pos, node_color='lightblue', 
                                 node_size=3000, alpha=0.7)
            
            # Dibujar aristas con grosor proporcional al peso
            edges = G.edges()
            weights = [G[u][v]['weight'] for u, v in edges]
            max_weight = max(weights) if weights else 1
            
            nx.draw_networkx_edges(G, pos, width=[w/max_weight * 5 for w in weights],
                                 alpha=0.6, edge_color='gray', arrows=True,
                                 arrowsize=20, arrowstyle='->')
            
            # Dibujar etiquetas
            nx.draw_networkx_labels(G, pos, font_size=8, font_weight='bold')
            
            # Agregar etiquetas de peso en las aristas
            edge_labels = {(u, v): str(G[u][v]['weight']) for u, v in G.edges()}
            nx.draw_networkx_edge_labels(G, pos, edge_labels, font_size=6)
            
            plt.axis('off')
            plt.tight_layout()
            
            # Guardar imagen
            filename = f"{viz_type}_alternative_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            file_path = os.path.join(self.temp_dir, filename)
            plt.savefig(file_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            # Calcular métricas básicas
            num_activities = len(G.nodes())
            num_transitions = len(G.edges())
            
            return {
                'success': True,
                'image_path': file_path,
                'metrics': {
                    'Actividades': num_activities,
                    'Transiciones': num_transitions,
                    'Casos': df['case:concept:name'].nunique(),
                    'Eventos': len(df)
                },
                'warning': 'Visualización alternativa creada (Graphviz no disponible)'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Error al crear visualización alternativa: {str(e)}",
                'suggestion': 'Instale Graphviz para visualizaciones completas'
            }
    
    def get_installation_instructions(self):
        """Obtener instrucciones de instalación de Graphviz"""
        import platform
        
        system = platform.system().lower()
        
        instructions = {
            'darwin': {  # macOS
                'title': 'Instalación en macOS',
                'commands': [
                    'brew install graphviz',
                    'pip install graphviz'
                ],
                'note': 'Requiere Homebrew instalado'
            },
            'linux': {
                'title': 'Instalación en Linux',
                'commands': [
                    'sudo apt-get install graphviz graphviz-dev',  # Ubuntu/Debian
                    'sudo yum install graphviz graphviz-devel',    # CentOS/RHEL
                    'pip install graphviz'
                ],
                'note': 'Usar el comando apropiado para su distribución'
            },
            'windows': {
                'title': 'Instalación en Windows',
                'commands': [
                    'Descargar desde: https://graphviz.org/download/',
                    'Agregar a PATH: C:\\Program Files\\Graphviz\\bin',
                    'pip install graphviz'
                ],
                'note': 'Reiniciar terminal después de agregar a PATH'
            }
        }
        
        return instructions.get(system, instructions['linux'])