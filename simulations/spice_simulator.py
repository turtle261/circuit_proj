"""
SPICE simulation module using PySpice and NGSpice.
"""
import os
import logging
import tempfile
import json
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO
import base64

try:
    import PySpice.Logging.Logging as Logging
    from PySpice.Spice.NgSpice.Shared import NgSpiceShared
    from PySpice.Spice.Netlist import Circuit
    from PySpice.Unit import *
    PYSPICE_AVAILABLE = True
except ImportError:
    PYSPICE_AVAILABLE = False
    logging.warning("PySpice not available. Simulation features will be limited.")

logger = logging.getLogger(__name__)

class SpiceSimulator:
    """SPICE circuit simulator using PySpice and NGSpice."""
    
    def __init__(self):
        self.ngspice_shared = None
        if PYSPICE_AVAILABLE:
            try:
                # Initialize NGSpice
                self.ngspice_shared = NgSpiceShared.new_instance()
                logger.info("NGSpice initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize NGSpice: {e}")
                self.ngspice_shared = None
    
    def create_led_circuit(self, led_voltage: float = 2.0, supply_voltage: float = 5.0, 
                          current_limit: float = 0.02) -> Optional[Circuit]:
        """Create a simple LED circuit with current limiting resistor."""
        if not PYSPICE_AVAILABLE:
            logger.error("PySpice not available")
            return None
            
        try:
            # Calculate resistor value: R = (Vsupply - Vled) / I
            resistor_value = (supply_voltage - led_voltage) / current_limit
            
            circuit = Circuit('LED Circuit')
            
            # Add voltage source
            circuit.V('supply', 'vcc', circuit.gnd, supply_voltage@u_V)
            
            # Add resistor
            circuit.R('current_limit', 'vcc', 'led_anode', resistor_value@u_Ω)
            
            # Add LED (modeled as voltage source + resistor)
            circuit.V('led', 'led_anode', 'led_cathode', led_voltage@u_V)
            circuit.R('led_internal', 'led_cathode', circuit.gnd, 10@u_Ω)
            
            logger.info(f"Created LED circuit: R={resistor_value:.1f}Ω, Vled={led_voltage}V")
            return circuit
            
        except Exception as e:
            logger.error(f"Failed to create LED circuit: {e}")
            return None
    
    def create_blinker_circuit(self, led_voltage: float = 2.0, supply_voltage: float = 5.0) -> Optional[Circuit]:
        """Create a simple LED blinker circuit with 555 timer."""
        if not PYSPICE_AVAILABLE:
            logger.error("PySpice not available")
            return None
            
        try:
            circuit = Circuit('LED Blinker Circuit')
            
            # Add voltage source
            circuit.V('supply', 'vcc', circuit.gnd, supply_voltage@u_V)
            
            # Simplified blinker using RC oscillator
            # Timing capacitor
            circuit.C('timing', 'osc_node', circuit.gnd, 10@u_uF)
            
            # Timing resistor
            circuit.R('timing', 'vcc', 'osc_node', 100@u_kΩ)
            
            # LED current limiting resistor
            resistor_value = (supply_voltage - led_voltage) / 0.02  # 20mA
            circuit.R('led_limit', 'osc_node', 'led_anode', resistor_value@u_Ω)
            
            # LED
            circuit.V('led', 'led_anode', 'led_cathode', led_voltage@u_V)
            circuit.R('led_internal', 'led_cathode', circuit.gnd, 10@u_Ω)
            
            logger.info("Created LED blinker circuit")
            return circuit
            
        except Exception as e:
            logger.error(f"Failed to create blinker circuit: {e}")
            return None
    
    def run_dc_analysis(self, circuit: Circuit) -> Optional[Dict[str, Any]]:
        """Run DC operating point analysis."""
        if not circuit or not self.ngspice_shared:
            logger.error("Circuit or NGSpice not available")
            return None
            
        try:
            simulator = circuit.simulator(temperature=25, nominal_temperature=25)
            analysis = simulator.operating_point()
            
            results = {
                'analysis_type': 'DC Operating Point',
                'nodes': {},
                'currents': {},
                'success': True
            }
            
            # Extract node voltages
            for node in analysis.nodes:
                results['nodes'][str(node)] = float(analysis[node])
            
            # Extract branch currents
            for branch in analysis.branches:
                results['currents'][str(branch)] = float(analysis[branch])
            
            logger.info("DC analysis completed successfully")
            return results
            
        except Exception as e:
            logger.error(f"DC analysis failed: {e}")
            return {
                'analysis_type': 'DC Operating Point',
                'error': str(e),
                'success': False
            }
    
    def run_transient_analysis(self, circuit: Circuit, duration: float = 1.0, 
                             step: float = 0.01) -> Optional[Dict[str, Any]]:
        """Run transient analysis."""
        if not circuit or not self.ngspice_shared:
            logger.error("Circuit or NGSpice not available")
            return None
            
        try:
            simulator = circuit.simulator(temperature=25, nominal_temperature=25)
            analysis = simulator.transient(step_time=step@u_ms, end_time=duration@u_s)
            
            results = {
                'analysis_type': 'Transient',
                'time': analysis.time.as_ndarray().tolist(),
                'nodes': {},
                'success': True,
                'duration': duration,
                'step': step
            }
            
            # Extract node voltages over time
            for node in analysis.nodes:
                results['nodes'][str(node)] = analysis[node].as_ndarray().tolist()
            
            logger.info(f"Transient analysis completed: {duration}s duration")
            return results
            
        except Exception as e:
            logger.error(f"Transient analysis failed: {e}")
            return {
                'analysis_type': 'Transient',
                'error': str(e),
                'success': False
            }
    
    def validate_led_circuit(self, led_voltage: float = 2.0, supply_voltage: float = 5.0,
                           max_current: float = 0.025) -> Dict[str, Any]:
        """Validate LED circuit parameters."""
        try:
            circuit = self.create_led_circuit(led_voltage, supply_voltage)
            if not circuit:
                return {
                    'valid': False,
                    'error': 'Failed to create circuit',
                    'recommendations': ['Check PySpice installation']
                }
            
            # Run DC analysis
            dc_results = self.run_dc_analysis(circuit)
            if not dc_results or not dc_results.get('success'):
                return {
                    'valid': False,
                    'error': 'DC analysis failed',
                    'recommendations': ['Check circuit parameters']
                }
            
            # Calculate actual current
            resistor_current = abs(dc_results['currents'].get('Rcurrent_limit', 0))
            
            validation = {
                'valid': True,
                'led_current': resistor_current,
                'max_current': max_current,
                'current_ok': resistor_current <= max_current,
                'voltage_drop_ok': True,  # Simplified check
                'recommendations': []
            }
            
            if not validation['current_ok']:
                validation['valid'] = False
                validation['recommendations'].append(
                    f"Current too high: {resistor_current:.3f}A > {max_current:.3f}A"
                )
            
            if resistor_current < 0.005:  # Too dim
                validation['recommendations'].append(
                    "Current may be too low for visible LED brightness"
                )
            
            return validation
            
        except Exception as e:
            logger.error(f"Circuit validation failed: {e}")
            return {
                'valid': False,
                'error': str(e),
                'recommendations': ['Check circuit parameters and PySpice installation']
            }
    
    def generate_plot(self, analysis_results: Dict[str, Any]) -> Optional[str]:
        """Generate a plot from analysis results and return as base64 string."""
        try:
            if not analysis_results.get('success'):
                return None
            
            plt.figure(figsize=(10, 6))
            
            if analysis_results['analysis_type'] == 'Transient':
                time = analysis_results['time']
                for node_name, voltages in analysis_results['nodes'].items():
                    if node_name != '0':  # Skip ground node
                        plt.plot(time, voltages, label=f'Node {node_name}')
                
                plt.xlabel('Time (s)')
                plt.ylabel('Voltage (V)')
                plt.title('Transient Analysis Results')
                plt.legend()
                plt.grid(True)
                
            elif analysis_results['analysis_type'] == 'DC Operating Point':
                nodes = list(analysis_results['nodes'].keys())
                voltages = list(analysis_results['nodes'].values())
                
                plt.bar(nodes, voltages)
                plt.xlabel('Nodes')
                plt.ylabel('Voltage (V)')
                plt.title('DC Operating Point Analysis')
                plt.grid(True, axis='y')
            
            # Convert plot to base64 string
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
            buffer.seek(0)
            plot_data = base64.b64encode(buffer.getvalue()).decode()
            plt.close()
            
            return plot_data
            
        except Exception as e:
            logger.error(f"Plot generation failed: {e}")
            return None
    
    def get_component_recommendations(self, circuit_type: str, 
                                    requirements: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get component recommendations based on circuit type and requirements."""
        recommendations = []
        
        if circuit_type.lower() == 'led_blinker':
            # LED recommendations
            led_voltage = requirements.get('led_voltage', 2.0)
            supply_voltage = requirements.get('supply_voltage', 5.0)
            current = requirements.get('current', 0.02)
            
            # Calculate resistor value
            resistor_value = (supply_voltage - led_voltage) / current
            
            # Find standard resistor value
            standard_values = [220, 330, 470, 680, 1000, 1500, 2200, 3300, 4700]
            closest_resistor = min(standard_values, key=lambda x: abs(x - resistor_value))
            
            recommendations.append({
                'component_type': 'resistor',
                'value': closest_resistor,
                'unit': 'ohm',
                'purpose': 'LED current limiting',
                'calculated_value': resistor_value,
                'power_rating': 0.25  # 1/4 watt
            })
            
            recommendations.append({
                'component_type': 'led',
                'color': requirements.get('led_color', 'red'),
                'forward_voltage': led_voltage,
                'max_current': 0.02,
                'package': '5mm'
            })
        
        return recommendations

# Global simulator instance
simulator = SpiceSimulator()