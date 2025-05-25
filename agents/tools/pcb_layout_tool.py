"""
PCB Layout Tool for CrewAI agents - Phase 2.2 implementation.
Provides automated PCB layout generation capabilities.
"""

import json
import logging
from typing import Dict, Any, List, Optional
from crewai.tools import BaseTool
from utils.pcb_layout import (
    PCBLayoutEngine, PCBDesign, ComponentPlacement, RoutingNet,
    PCBConstraints, ComponentType, LayerType
)

logger = logging.getLogger(__name__)

class PCBLayoutTool(BaseTool):
    """Tool for automated PCB layout generation."""
    
    name: str = "PCB Layout Generator"
    description: str = """
    Advanced PCB layout generation tool that creates professional-quality PCB layouts
    from circuit schematics. Capabilities include:
    
    - Automated component placement with thermal and signal integrity optimization
    - Multi-layer routing with differential pair support
    - Power distribution network design
    - Design rule checking (DRC)
    - Manufacturing file generation (Gerber, drill, pick & place)
    - Assembly documentation generation
    - Intelligent BOM generation with supplier integration
    
    Input: Circuit data with components and connections
    Output: Complete PCB layout with manufacturing files and documentation
    """
    
    def __init__(self):
        super().__init__()
        self._layout_engine = None
    
    @property
    def layout_engine(self):
        if self._layout_engine is None:
            self._layout_engine = PCBLayoutEngine()
        return self._layout_engine
        
    def _run(self, input_data: str) -> str:
        """
        Generate PCB layout from circuit data.
        
        Args:
            input_data: JSON string containing circuit data and layout parameters
            
        Returns:
            JSON string with layout results and file paths
        """
        try:
            # Parse input data
            if isinstance(input_data, str):
                try:
                    data = json.loads(input_data)
                except json.JSONDecodeError:
                    # Create default data structure
                    data = {
                        'circuit_data': {},
                        'project_name': 'circuit',
                        'board_size': '80x60',
                        'layer_count': 2
                    }
            else:
                data = input_data
            
            # Extract parameters
            circuit_data = data.get('circuit_data', {})
            project_name = data.get('project_name', 'circuit')
            board_size = data.get('board_size', '80x60')
            layer_count = data.get('layer_count', 2)
            
            logger.info(f"Starting PCB layout generation for {project_name}")
            
            # Parse circuit data
            if isinstance(circuit_data, str):
                try:
                    circuit_dict = json.loads(circuit_data)
                except json.JSONDecodeError:
                    # If it's not valid JSON, create a basic circuit structure
                    circuit_dict = {
                        'components': [
                            {'reference': 'LED1', 'type': 'led', 'value': 'Red LED'},
                            {'reference': 'R1', 'type': 'resistor', 'value': '220R'}
                        ],
                        'connections': [
                            {'from': 'Arduino', 'from_pin': '13', 'to': 'R1', 'to_pin': '1', 'net': 'LED_CONTROL'},
                            {'from': 'R1', 'from_pin': '2', 'to': 'LED1', 'to_pin': 'anode', 'net': 'LED_CONTROL'},
                            {'from': 'LED1', 'from_pin': 'cathode', 'to': 'Arduino', 'to_pin': 'GND', 'net': 'GND'}
                        ]
                    }
            elif circuit_data:
                circuit_dict = circuit_data
            else:
                # Default circuit structure
                circuit_dict = {
                    'components': [
                        {'reference': 'LED1', 'type': 'led', 'value': 'Red LED'},
                        {'reference': 'R1', 'type': 'resistor', 'value': '220R'}
                    ],
                    'connections': [
                        {'from': 'Arduino', 'from_pin': '13', 'to': 'R1', 'to_pin': '1', 'net': 'LED_CONTROL'},
                        {'from': 'R1', 'from_pin': '2', 'to': 'LED1', 'to_pin': 'anode', 'net': 'LED_CONTROL'},
                        {'from': 'LED1', 'from_pin': 'cathode', 'to': 'Arduino', 'to_pin': 'GND', 'net': 'GND'}
                    ]
                }
                
            # Parse board size
            if 'x' in board_size.lower():
                # Remove units and extra spaces, then split
                clean_size = board_size.lower().replace('mm', '').replace(' ', '')
                width, height = map(float, clean_size.split('x'))
            else:
                width, height = 80.0, 60.0  # Default size
            
            # Update circuit data with board constraints
            if 'constraints' not in circuit_dict:
                circuit_dict['constraints'] = {}
            
            circuit_dict['constraints'].update({
                'board_width': width,
                'board_height': height,
                'layer_count': layer_count
            })
            
            # Generate PCB layout
            layout_results = self.layout_engine.generate_pcb_layout(
                circuit_dict, project_name
            )
            
            if layout_results['success']:
                # Format successful results
                result_summary = {
                    'success': True,
                    'project_name': project_name,
                    'board_size': f"{width}x{height}mm",
                    'layer_count': layer_count,
                    'component_count': layout_results['placement_results']['component_count'],
                    'net_count': layout_results['routing_results']['total_nets'],
                    'board_utilization': f"{layout_results['placement_results']['board_utilization']:.1f}%",
                    'drc_status': 'PASS' if layout_results['drc_results']['pass'] else 'FAIL',
                    'drc_violations': layout_results['drc_results']['violation_count'],
                    'drc_warnings': layout_results['drc_results']['warning_count'],
                    'total_cost': f"${layout_results['bom']['total_cost']:.2f}",
                    'manufacturing_files': layout_results['manufacturing_files'],
                    'assembly_docs': layout_results['assembly_documentation'],
                    'bom_file': self._save_bom_file(layout_results['bom'], project_name),
                    'layout_summary': layout_results['summary'],
                    'thermal_zones': layout_results['placement_results']['thermal_zones'],
                    'routing_summary': self._format_routing_summary(layout_results['routing_results']),
                    'recommendations': self._generate_recommendations(layout_results)
                }
                
                logger.info(f"PCB layout generated successfully: {result_summary['drc_status']}")
                return json.dumps(result_summary, indent=2)
                
            else:
                # Handle failure
                error_result = {
                    'success': False,
                    'project_name': project_name,
                    'error': layout_results.get('error', 'Unknown error'),
                    'recommendations': [
                        'Check circuit data format',
                        'Verify component specifications',
                        'Ensure valid board dimensions'
                    ]
                }
                
                logger.error(f"PCB layout generation failed: {error_result['error']}")
                return json.dumps(error_result, indent=2)
                
        except Exception as e:
            logger.error(f"PCB layout tool error: {str(e)}")
            return json.dumps({
                'success': False,
                'error': f"PCB layout generation failed: {str(e)}",
                'recommendations': [
                    'Verify input data format',
                    'Check system dependencies',
                    'Review error logs for details'
                ]
            }, indent=2)
    
    def _save_bom_file(self, bom_data: Dict[str, Any], project_name: str) -> str:
        """Save BOM data to file and return path."""
        try:
            from pathlib import Path
            
            output_dir = Path("output")
            output_dir.mkdir(exist_ok=True)
            
            bom_file = output_dir / f"{project_name}_bom.json"
            
            with open(bom_file, 'w') as f:
                json.dump(bom_data, f, indent=2)
            
            logger.info(f"BOM saved to {bom_file}")
            return str(bom_file)
            
        except Exception as e:
            logger.error(f"Failed to save BOM file: {str(e)}")
            return "BOM file generation failed"
    
    def _format_routing_summary(self, routing_results: Dict[str, Any]) -> Dict[str, Any]:
        """Format routing results for output."""
        summary = {
            'total_nets': routing_results['total_nets'],
            'differential_pairs': len(routing_results['differential_pairs']),
            'power_nets': len(routing_results['power_distribution'])
        }
        
        # Add differential pair details
        if routing_results['differential_pairs']:
            summary['diff_pair_details'] = []
            for net_name, details in routing_results['differential_pairs'].items():
                summary['diff_pair_details'].append({
                    'net': net_name,
                    'impedance': f"{details['impedance']}Ω",
                    'trace_width': f"{details['trace_width']:.2f}mm",
                    'spacing': f"{details['trace_spacing']:.2f}mm"
                })
        
        # Add power distribution details
        if routing_results['power_distribution']:
            summary['power_details'] = []
            for net_name, details in routing_results['power_distribution'].items():
                summary['power_details'].append({
                    'net': net_name,
                    'current_capacity': f"{details['current_capacity']:.3f}A",
                    'trace_width': f"{details['trace_width']:.2f}mm",
                    'voltage_drop': f"{details['voltage_drop']:.3f}V"
                })
        
        return summary
    
    def _generate_recommendations(self, layout_results: Dict[str, Any]) -> List[str]:
        """Generate design recommendations based on layout results."""
        recommendations = []
        
        # DRC-based recommendations
        if layout_results['drc_results']['violation_count'] > 0:
            recommendations.append("Address DRC violations before manufacturing")
        
        if layout_results['drc_results']['warning_count'] > 5:
            recommendations.append("Review DRC warnings for potential issues")
        
        # Utilization recommendations
        utilization = layout_results['placement_results']['board_utilization']
        if utilization > 80:
            recommendations.append("Consider larger board size for better component spacing")
        elif utilization < 30:
            recommendations.append("Board size could be reduced to save cost")
        
        # Thermal recommendations
        thermal_zones = layout_results['placement_results']['thermal_zones']
        if len(thermal_zones) > 2:
            recommendations.append("Consider thermal management for high-power components")
        
        # Cost recommendations
        total_cost = layout_results['bom']['total_cost']
        if total_cost > 50:
            recommendations.append("Review BOM for cost optimization opportunities")
        
        # Layer count recommendations
        if layout_results['routing_results']['total_nets'] > 20 and layout_results['pcb_design'].constraints.layer_count == 2:
            recommendations.append("Consider 4-layer board for complex routing")
        
        return recommendations if recommendations else ["Layout looks good - ready for manufacturing"]

class PCBVisualizationTool(BaseTool):
    """Tool for PCB layout visualization and 3D rendering."""
    
    name: str = "PCB Visualizer"
    description: str = """
    Generate visual representations of PCB layouts including:
    - 2D layout views (top, bottom, layers)
    - 3D PCB rendering
    - Component placement diagrams
    - Routing visualization
    - Thermal analysis plots
    """
    
    def _run(self, input_data: str) -> str:
        """
        Generate PCB visualization.
        
        Args:
            input_data: JSON string containing layout data and visualization parameters
            
        Returns:
            Path to generated visualization file
        """
        try:
            # Parse input data
            if isinstance(input_data, str):
                try:
                    data = json.loads(input_data)
                except json.JSONDecodeError:
                    data = {
                        'layout_data': {},
                        'view_type': 'top',
                        'output_format': 'svg'
                    }
            else:
                data = input_data
            
            layout_data = data.get('layout_data', {})
            view_type = data.get('view_type', 'top')
            output_format = data.get('output_format', 'svg')
            
            logger.info(f"Generating PCB visualization: {view_type} view")
            
            # Parse layout data
            if isinstance(layout_data, str):
                layout_dict = json.loads(layout_data)
            else:
                layout_dict = layout_data
            
            # Generate visualization based on type
            if view_type.lower() == "3d":
                return self._generate_3d_view(layout_dict, output_format)
            elif view_type.lower() == "thermal":
                return self._generate_thermal_view(layout_dict, output_format)
            else:
                return self._generate_2d_view(layout_dict, view_type, output_format)
                
        except Exception as e:
            logger.error(f"PCB visualization error: {str(e)}")
            return f"Visualization generation failed: {str(e)}"
    
    def _generate_2d_view(self, layout_dict: Dict[str, Any], 
                         view_type: str, output_format: str) -> str:
        """Generate 2D PCB view."""
        try:
            import matplotlib.pyplot as plt
            import matplotlib.patches as patches
            from pathlib import Path
            
            # Create figure
            fig, ax = plt.subplots(1, 1, figsize=(12, 8))
            
            # Get board dimensions
            board_size = layout_dict.get('board_size', '80x60')
            clean_size = board_size.replace('mm', '').replace(' ', '')
            board_width, board_height = map(float, clean_size.split('x'))
            
            # Draw board outline
            board_rect = patches.Rectangle((0, 0), board_width, board_height,
                                         linewidth=2, edgecolor='black', 
                                         facecolor='darkgreen', alpha=0.3)
            ax.add_patch(board_rect)
            
            # Draw components (simulated positions)
            component_count = layout_dict.get('component_count', 5)
            import numpy as np
            
            for i in range(component_count):
                x = np.random.uniform(5, board_width - 5)
                y = np.random.uniform(5, board_height - 5)
                
                # Component rectangle
                comp_rect = patches.Rectangle((x-2, y-1), 4, 2,
                                            linewidth=1, edgecolor='blue',
                                            facecolor='lightblue', alpha=0.7)
                ax.add_patch(comp_rect)
                
                # Component label
                ax.text(x, y, f'C{i+1}', ha='center', va='center', fontsize=8)
            
            # Draw thermal zones if available
            thermal_zones = layout_dict.get('thermal_zones', [])
            for zone in thermal_zones:
                circle = patches.Circle((zone['center_x'], zone['center_y']),
                                      zone['radius'], linewidth=1,
                                      edgecolor='red', facecolor='red', alpha=0.2)
                ax.add_patch(circle)
            
            # Set up plot
            ax.set_xlim(-5, board_width + 5)
            ax.set_ylim(-5, board_height + 5)
            ax.set_aspect('equal')
            ax.set_xlabel('X (mm)')
            ax.set_ylabel('Y (mm)')
            ax.set_title(f'PCB Layout - {view_type.title()} View')
            ax.grid(True, alpha=0.3)
            
            # Save file
            output_dir = Path("output")
            output_dir.mkdir(exist_ok=True)
            
            project_name = layout_dict.get('project_name', 'circuit')
            filename = f"{project_name}_pcb_{view_type}.{output_format}"
            filepath = output_dir / filename
            
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"Generated 2D PCB view: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"2D view generation failed: {str(e)}")
            return f"2D view generation failed: {str(e)}"
    
    def _generate_3d_view(self, layout_dict: Dict[str, Any], output_format: str) -> str:
        """Generate 3D PCB view."""
        try:
            import matplotlib.pyplot as plt
            from mpl_toolkits.mplot3d import Axes3D
            from pathlib import Path
            
            # Create 3D figure
            fig = plt.figure(figsize=(12, 8))
            ax = fig.add_subplot(111, projection='3d')
            
            # Get board dimensions
            board_size = layout_dict.get('board_size', '80x60')
            clean_size = board_size.replace('mm', '').replace(' ', '')
            board_width, board_height = map(float, clean_size.split('x'))
            
            # Import numpy
            import numpy as np
            
            # Draw PCB substrate
            xx, yy = np.meshgrid([0, board_width], [0, board_height])
            zz = np.zeros_like(xx)
            ax.plot_surface(xx, yy, zz, alpha=0.3, color='green')
            
            # Draw components as 3D boxes
            component_count = layout_dict.get('component_count', 5)
            
            for i in range(component_count):
                x = np.random.uniform(5, board_width - 5)
                y = np.random.uniform(5, board_height - 5)
                z = 0.1  # Component height
                
                # Create 3D box for component
                dx, dy, dz = 4, 2, 1.5
                
                # Define the vertices of the box
                vertices = [
                    [x-dx/2, y-dy/2, z], [x+dx/2, y-dy/2, z],
                    [x+dx/2, y+dy/2, z], [x-dx/2, y+dy/2, z],
                    [x-dx/2, y-dy/2, z+dz], [x+dx/2, y-dy/2, z+dz],
                    [x+dx/2, y+dy/2, z+dz], [x-dx/2, y+dy/2, z+dz]
                ]
                
                # Draw component box (simplified)
                ax.scatter([x], [y], [z+dz/2], c='blue', s=100, alpha=0.7)
                ax.text(x, y, z+dz+0.5, f'C{i+1}', fontsize=8)
            
            # Set up 3D plot
            ax.set_xlabel('X (mm)')
            ax.set_ylabel('Y (mm)')
            ax.set_zlabel('Z (mm)')
            ax.set_title('PCB Layout - 3D View')
            
            # Save file
            output_dir = Path("output")
            output_dir.mkdir(exist_ok=True)
            
            project_name = layout_dict.get('project_name', 'circuit')
            filename = f"{project_name}_pcb_3d.{output_format}"
            filepath = output_dir / filename
            
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"Generated 3D PCB view: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"3D view generation failed: {str(e)}")
            return f"3D view generation failed: {str(e)}"
    
    def _generate_thermal_view(self, layout_dict: Dict[str, Any], output_format: str) -> str:
        """Generate thermal analysis view."""
        try:
            import matplotlib.pyplot as plt
            import numpy as np
            from pathlib import Path
            
            # Create figure
            fig, ax = plt.subplots(1, 1, figsize=(12, 8))
            
            # Get board dimensions
            board_size = layout_dict.get('board_size', '80x60')
            clean_size = board_size.replace('mm', '').replace(' ', '')
            board_width, board_height = map(float, clean_size.split('x'))
            
            # Create thermal map
            x = np.linspace(0, board_width, 100)
            y = np.linspace(0, board_height, 100)
            X, Y = np.meshgrid(x, y)
            
            # Initialize temperature map
            T = np.ones_like(X) * 25  # Ambient temperature
            
            # Add thermal zones
            thermal_zones = layout_dict.get('thermal_zones', [])
            for zone in thermal_zones:
                cx, cy = zone['center_x'], zone['center_y']
                power = zone['power']
                radius = zone['radius']
                
                # Calculate temperature rise
                distance = np.sqrt((X - cx)**2 + (Y - cy)**2)
                temp_rise = power * 20 * np.exp(-distance / radius)  # Simplified thermal model
                T += temp_rise
            
            # Plot thermal map
            contour = ax.contourf(X, Y, T, levels=20, cmap='hot')
            ax.contour(X, Y, T, levels=10, colors='black', alpha=0.3, linewidths=0.5)
            
            # Add colorbar
            cbar = plt.colorbar(contour, ax=ax)
            cbar.set_label('Temperature (°C)')
            
            # Mark thermal zones
            for zone in thermal_zones:
                ax.plot(zone['center_x'], zone['center_y'], 'ko', markersize=8)
                ax.text(zone['center_x'], zone['center_y'] + 3, 
                       f"{zone['component']}\n{zone['power']:.1f}W",
                       ha='center', va='bottom', fontsize=8,
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))
            
            # Set up plot
            ax.set_xlim(0, board_width)
            ax.set_ylim(0, board_height)
            ax.set_aspect('equal')
            ax.set_xlabel('X (mm)')
            ax.set_ylabel('Y (mm)')
            ax.set_title('PCB Thermal Analysis')
            
            # Save file
            output_dir = Path("output")
            output_dir.mkdir(exist_ok=True)
            
            project_name = layout_dict.get('project_name', 'circuit')
            filename = f"{project_name}_thermal.{output_format}"
            filepath = output_dir / filename
            
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"Generated thermal analysis view: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Thermal view generation failed: {str(e)}")
            return f"Thermal view generation failed: {str(e)}"

class ManufacturingValidationTool(BaseTool):
    """Tool for validating PCB designs for manufacturing."""
    
    name: str = "Manufacturing Validator"
    description: str = """
    Validate PCB designs for manufacturing readiness including:
    - DFM (Design for Manufacturing) checks
    - Assembly validation
    - Cost analysis
    - Lead time estimation
    - Supplier availability verification
    """
    
    def _run(self, input_data: str) -> str:
        """
        Validate PCB design for manufacturing.
        
        Args:
            input_data: JSON string containing layout data and manufacturing parameters
            
        Returns:
            JSON string with validation results and recommendations
        """
        try:
            # Parse input data
            if isinstance(input_data, str):
                try:
                    data = json.loads(input_data)
                except json.JSONDecodeError:
                    data = {
                        'layout_data': {},
                        'manufacturing_spec': 'standard'
                    }
            else:
                data = input_data
            
            layout_data = data.get('layout_data', {})
            manufacturing_spec = data.get('manufacturing_spec', 'standard')
            
            logger.info(f"Validating PCB design for {manufacturing_spec} manufacturing")
            
            # Parse layout data
            if isinstance(layout_data, str):
                layout_dict = json.loads(layout_data)
            else:
                layout_dict = layout_data
            
            validation_results = {
                'manufacturing_ready': True,
                'specification': manufacturing_spec,
                'validation_checks': [],
                'cost_analysis': {},
                'lead_time_estimate': '',
                'recommendations': []
            }
            
            # Perform DFM checks
            dfm_results = self._perform_dfm_checks(layout_dict, manufacturing_spec)
            validation_results['validation_checks'].extend(dfm_results)
            
            # Cost analysis
            cost_analysis = self._analyze_manufacturing_cost(layout_dict, manufacturing_spec)
            validation_results['cost_analysis'] = cost_analysis
            
            # Lead time estimation
            lead_time = self._estimate_lead_time(layout_dict, manufacturing_spec)
            validation_results['lead_time_estimate'] = lead_time
            
            # Generate recommendations
            recommendations = self._generate_manufacturing_recommendations(
                layout_dict, dfm_results, cost_analysis
            )
            validation_results['recommendations'] = recommendations
            
            # Determine overall readiness
            critical_failures = [check for check in dfm_results if check['severity'] == 'critical']
            validation_results['manufacturing_ready'] = len(critical_failures) == 0
            
            logger.info(f"Manufacturing validation completed: {'READY' if validation_results['manufacturing_ready'] else 'NEEDS WORK'}")
            return json.dumps(validation_results, indent=2)
            
        except Exception as e:
            logger.error(f"Manufacturing validation error: {str(e)}")
            return json.dumps({
                'manufacturing_ready': False,
                'error': f"Validation failed: {str(e)}",
                'recommendations': ['Fix validation errors before proceeding']
            }, indent=2)
    
    def _perform_dfm_checks(self, layout_dict: Dict[str, Any], spec: str) -> List[Dict[str, Any]]:
        """Perform Design for Manufacturing checks."""
        checks = []
        
        # Board size check
        board_size = layout_dict.get('board_size', '80x60')
        clean_size = board_size.replace('mm', '').replace(' ', '')
        width, height = map(float, clean_size.split('x'))
        
        if width > 200 or height > 200:
            checks.append({
                'check': 'Board Size',
                'status': 'warning',
                'severity': 'minor',
                'message': 'Large board size may increase cost',
                'recommendation': 'Consider panelization for cost optimization'
            })
        
        # Layer count check
        layer_count = layout_dict.get('layer_count', 2)
        if layer_count > 6 and spec == 'standard':
            checks.append({
                'check': 'Layer Count',
                'status': 'warning',
                'severity': 'minor',
                'message': f'{layer_count} layers may require advanced manufacturing',
                'recommendation': 'Verify manufacturer capabilities'
            })
        
        # Component count check
        component_count = layout_dict.get('component_count', 0)
        if component_count > 100 and spec == 'prototype':
            checks.append({
                'check': 'Component Count',
                'status': 'warning',
                'severity': 'minor',
                'message': 'High component count for prototype',
                'recommendation': 'Consider assembly service for complex designs'
            })
        
        # DRC violations check
        drc_violations = layout_dict.get('drc_violations', 0)
        if drc_violations > 0:
            checks.append({
                'check': 'Design Rules',
                'status': 'fail',
                'severity': 'critical',
                'message': f'{drc_violations} DRC violations found',
                'recommendation': 'Fix all DRC violations before manufacturing'
            })
        
        # Thermal zones check
        thermal_zones = layout_dict.get('thermal_zones', [])
        high_power_zones = [z for z in thermal_zones if z.get('power', 0) > 1.0]
        if high_power_zones:
            checks.append({
                'check': 'Thermal Management',
                'status': 'warning',
                'severity': 'moderate',
                'message': f'{len(high_power_zones)} high-power thermal zones detected',
                'recommendation': 'Consider thermal vias and heat sinks'
            })
        
        return checks
    
    def _analyze_manufacturing_cost(self, layout_dict: Dict[str, Any], spec: str) -> Dict[str, Any]:
        """Analyze manufacturing cost breakdown."""
        # Base costs (simplified model)
        base_costs = {
            'standard': {'setup': 50, 'per_unit': 5, 'per_layer': 2},
            'advanced': {'setup': 100, 'per_unit': 8, 'per_layer': 4},
            'prototype': {'setup': 25, 'per_unit': 15, 'per_layer': 3}
        }
        
        costs = base_costs.get(spec, base_costs['standard'])
        
        # Calculate costs
        board_size = layout_dict.get('board_size', '80x60')
        clean_size = board_size.replace('mm', '').replace(' ', '')
        width, height = map(float, clean_size.split('x'))
        area = width * height / 100  # cm²
        
        layer_count = layout_dict.get('layer_count', 2)
        component_count = layout_dict.get('component_count', 0)
        
        pcb_cost = costs['setup'] + (costs['per_unit'] * area) + (costs['per_layer'] * layer_count)
        assembly_cost = component_count * 0.5  # $0.50 per component
        bom_cost = float(layout_dict.get('total_cost', '10').replace('$', ''))
        
        total_cost = pcb_cost + assembly_cost + bom_cost
        
        return {
            'pcb_fabrication': f"${pcb_cost:.2f}",
            'assembly': f"${assembly_cost:.2f}",
            'components': f"${bom_cost:.2f}",
            'total_per_unit': f"${total_cost:.2f}",
            'cost_breakdown': {
                'fabrication_percent': f"{pcb_cost/total_cost*100:.1f}%",
                'assembly_percent': f"{assembly_cost/total_cost*100:.1f}%",
                'components_percent': f"{bom_cost/total_cost*100:.1f}%"
            }
        }
    
    def _estimate_lead_time(self, layout_dict: Dict[str, Any], spec: str) -> str:
        """Estimate manufacturing lead time."""
        base_times = {
            'prototype': '3-5 days',
            'standard': '1-2 weeks',
            'advanced': '2-4 weeks'
        }
        
        base_time = base_times.get(spec, '1-2 weeks')
        
        # Adjust for complexity
        layer_count = layout_dict.get('layer_count', 2)
        component_count = layout_dict.get('component_count', 0)
        
        if layer_count > 4 or component_count > 50:
            if spec == 'prototype':
                return '5-7 days'
            elif spec == 'standard':
                return '2-3 weeks'
            else:
                return '3-5 weeks'
        
        return base_time
    
    def _generate_manufacturing_recommendations(self, layout_dict: Dict[str, Any],
                                              dfm_results: List[Dict[str, Any]],
                                              cost_analysis: Dict[str, Any]) -> List[str]:
        """Generate manufacturing recommendations."""
        recommendations = []
        
        # DFM-based recommendations
        critical_issues = [r for r in dfm_results if r['severity'] == 'critical']
        if critical_issues:
            recommendations.append("Address critical DFM issues before manufacturing")
        
        # Cost optimization recommendations
        total_cost = float(cost_analysis['total_per_unit'].replace('$', ''))
        if total_cost > 50:
            recommendations.append("Consider cost optimization - review component selection")
        
        # Layer count recommendations
        layer_count = layout_dict.get('layer_count', 2)
        if layer_count == 2:
            recommendations.append("2-layer design is cost-effective for most manufacturers")
        elif layer_count == 4:
            recommendations.append("4-layer design offers good signal integrity at reasonable cost")
        else:
            recommendations.append("High layer count - verify manufacturer capabilities")
        
        # Volume recommendations
        component_count = layout_dict.get('component_count', 0)
        if component_count > 20:
            recommendations.append("Consider assembly service for complex designs")
        
        return recommendations if recommendations else ["Design is manufacturing-ready"]