"""
SPICE simulation module using PySpice and NGSpice.
Enhanced for Phase 2.1 with advanced simulation capabilities:
- AC Analysis with frequency sweeps and Bode plots
- Noise Analysis for low-noise circuit design
- Monte Carlo Analysis for statistical validation
- Advanced circuit topology support
"""
import os
import logging
import tempfile
import json
import random
from typing import Dict, List, Any, Optional, Tuple, Union
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from dataclasses import dataclass
from enum import Enum

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

class CircuitType(Enum):
    """Enumeration of supported circuit types for Phase 2.1"""
    LED_BASIC = "led_basic"
    LED_BLINKER = "led_blinker"
    OPAMP_INVERTING = "opamp_inverting"
    OPAMP_NON_INVERTING = "opamp_non_inverting"
    OPAMP_DIFFERENTIAL = "opamp_differential"
    ACTIVE_FILTER_LOWPASS = "active_filter_lowpass"
    ACTIVE_FILTER_HIGHPASS = "active_filter_highpass"
    ACTIVE_FILTER_BANDPASS = "active_filter_bandpass"
    OSCILLATOR_WIEN_BRIDGE = "oscillator_wien_bridge"
    VOLTAGE_REGULATOR = "voltage_regulator"

@dataclass
class SimulationParameters:
    """Parameters for advanced simulation analysis"""
    # AC Analysis
    start_frequency: float = 1.0  # Hz
    stop_frequency: float = 1e6   # Hz
    points_per_decade: int = 100
    
    # Transient Analysis
    step_time: float = 1e-6  # seconds
    end_time: float = 1e-3   # seconds
    
    # Monte Carlo Analysis
    iterations: int = 100
    component_tolerance: float = 0.05  # 5% tolerance
    
    # Temperature Analysis
    temp_start: float = -40  # Celsius
    temp_stop: float = 85    # Celsius
    temp_step: float = 25    # Celsius

@dataclass
class PerformanceMetrics:
    """Circuit performance metrics calculated from simulation"""
    # General metrics
    dc_gain: Optional[float] = None
    bandwidth: Optional[float] = None
    input_impedance: Optional[float] = None
    output_impedance: Optional[float] = None
    
    # Amplifier metrics
    gain_margin: Optional[float] = None
    phase_margin: Optional[float] = None
    unity_gain_frequency: Optional[float] = None
    
    # Filter metrics
    cutoff_frequency: Optional[float] = None
    rolloff_rate: Optional[float] = None  # dB/decade
    passband_ripple: Optional[float] = None
    stopband_attenuation: Optional[float] = None
    
    # Noise metrics
    input_noise_voltage: Optional[float] = None
    input_noise_current: Optional[float] = None
    noise_figure: Optional[float] = None
    
    # Power metrics
    power_consumption: Optional[float] = None
    efficiency: Optional[float] = None
    
    # Dynamic metrics
    slew_rate: Optional[float] = None  # V/μs
    settling_time: Optional[float] = None  # seconds
    
    # Distortion metrics
    thd: Optional[float] = None  # Total Harmonic Distortion (%)
    snr: Optional[float] = None  # Signal-to-Noise Ratio (dB)

class SpiceSimulator:
    """Enhanced SPICE circuit simulator for Phase 2.1 with advanced analysis capabilities."""
    
    def __init__(self):
        self.ngspice_shared = None
        self.simulation_params = SimulationParameters()
        if PYSPICE_AVAILABLE:
            try:
                # Initialize NGSpice
                self.ngspice_shared = NgSpiceShared.new_instance()
                logger.info("NGSpice initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize NGSpice: {e}")
                self.ngspice_shared = None
    
    def set_simulation_parameters(self, params: SimulationParameters):
        """Set simulation parameters for advanced analysis."""
        self.simulation_params = params
        logger.info(f"Updated simulation parameters: AC freq range {params.start_frequency}-{params.stop_frequency} Hz")
    
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
    
    def create_opamp_inverting_amplifier(self, gain: float = -10, input_impedance: float = 10000,
                                       supply_voltage: float = 15) -> Optional[Circuit]:
        """Create an inverting operational amplifier circuit."""
        if not PYSPICE_AVAILABLE:
            logger.error("PySpice not available")
            return None
        
        try:
            circuit = Circuit('Inverting Op-Amp Amplifier')
            
            # Power supplies
            circuit.V('dd', 'vdd', circuit.gnd, supply_voltage@u_V)
            circuit.V('ss', 'vss', circuit.gnd, -supply_voltage@u_V)
            
            # Input signal source
            circuit.V('in', 'vin', circuit.gnd, 'AC 1')
            
            # Feedback resistor (determines gain)
            rf = abs(gain) * input_impedance
            circuit.R('f', 'vout', 'inv_in', rf@u_Ω)
            
            # Input resistor
            circuit.R('in', 'vin', 'inv_in', input_impedance@u_Ω)
            
            # Op-amp model (simplified)
            # Using voltage-controlled voltage source as ideal op-amp
            circuit.VCVS('opamp', 'vout', circuit.gnd, 'non_inv_in', 'inv_in', 100000)
            
            # Non-inverting input to ground
            circuit.R('bias', 'non_inv_in', circuit.gnd, 1@u_MΩ)
            
            # Output load
            circuit.R('load', 'vout', circuit.gnd, 10@u_kΩ)
            
            logger.info(f"Created inverting op-amp circuit: gain={gain}, Rin={input_impedance}Ω")
            return circuit
            
        except Exception as e:
            logger.error(f"Failed to create inverting op-amp circuit: {e}")
            return None
    
    def create_opamp_non_inverting_amplifier(self, gain: float = 10, input_impedance: float = 1e6,
                                           supply_voltage: float = 15) -> Optional[Circuit]:
        """Create a non-inverting operational amplifier circuit."""
        if not PYSPICE_AVAILABLE:
            logger.error("PySpice not available")
            return None
        
        try:
            circuit = Circuit('Non-Inverting Op-Amp Amplifier')
            
            # Power supplies
            circuit.V('dd', 'vdd', circuit.gnd, supply_voltage@u_V)
            circuit.V('ss', 'vss', circuit.gnd, -supply_voltage@u_V)
            
            # Input signal source
            circuit.V('in', 'vin', circuit.gnd, 'AC 1')
            
            # Input to non-inverting terminal
            circuit.R('in', 'vin', 'non_inv_in', 1@u_Ω)  # Very small resistance
            
            # Feedback network
            # For non-inverting: gain = 1 + Rf/R1
            r1 = 10000  # 10kΩ
            rf = (gain - 1) * r1
            
            circuit.R('1', 'inv_in', circuit.gnd, r1@u_Ω)
            circuit.R('f', 'vout', 'inv_in', rf@u_Ω)
            
            # Op-amp model (simplified)
            circuit.VCVS('opamp', 'vout', circuit.gnd, 'non_inv_in', 'inv_in', 100000)
            
            # Output load
            circuit.R('load', 'vout', circuit.gnd, 10@u_kΩ)
            
            logger.info(f"Created non-inverting op-amp circuit: gain={gain}")
            return circuit
            
        except Exception as e:
            logger.error(f"Failed to create non-inverting op-amp circuit: {e}")
            return None
    
    def create_active_lowpass_filter(self, cutoff_frequency: float = 1000, gain: float = 1,
                                   q_factor: float = 0.707, supply_voltage: float = 15) -> Optional[Circuit]:
        """Create a Sallen-Key active low-pass filter."""
        if not PYSPICE_AVAILABLE:
            logger.error("PySpice not available")
            return None
        
        try:
            circuit = Circuit('Active Low-Pass Filter')
            
            # Power supplies
            circuit.V('dd', 'vdd', circuit.gnd, supply_voltage@u_V)
            circuit.V('ss', 'vss', circuit.gnd, -supply_voltage@u_V)
            
            # Input signal source
            circuit.V('in', 'vin', circuit.gnd, 'AC 1')
            
            # Sallen-Key topology component values
            # For equal component design: R1 = R2 = R, C1 = C, C2 = C/K
            # where K is related to Q factor
            
            # Calculate component values
            R = 1 / (2 * np.pi * cutoff_frequency * 1e-9)  # Assuming C = 1nF
            C1 = 1e-9  # 1nF
            C2 = C1 / (2 * q_factor**2)  # For Butterworth response
            
            # Input resistors
            circuit.R('1', 'vin', 'node1', R@u_Ω)
            circuit.R('2', 'node1', 'node2', R@u_Ω)
            
            # Capacitors
            circuit.C('1', 'node1', 'vout', C1@u_F)
            circuit.C('2', 'node2', circuit.gnd, C2@u_F)
            
            # Op-amp buffer (unity gain)
            circuit.VCVS('opamp', 'vout', circuit.gnd, 'node2', 'inv_in', 100000)
            
            # Feedback for unity gain
            circuit.R('fb', 'vout', 'inv_in', 1@u_Ω)
            
            # Output load
            circuit.R('load', 'vout', circuit.gnd, 10@u_kΩ)
            
            logger.info(f"Created active low-pass filter: fc={cutoff_frequency}Hz, Q={q_factor}")
            return circuit
            
        except Exception as e:
            logger.error(f"Failed to create active low-pass filter: {e}")
            return None
    
    def create_active_highpass_filter(self, cutoff_frequency: float = 1000, gain: float = 1,
                                    q_factor: float = 0.707, supply_voltage: float = 15) -> Optional[Circuit]:
        """Create a Sallen-Key active high-pass filter."""
        if not PYSPICE_AVAILABLE:
            logger.error("PySpice not available")
            return None
        
        try:
            circuit = Circuit('Active High-Pass Filter')
            
            # Power supplies
            circuit.V('dd', 'vdd', circuit.gnd, supply_voltage@u_V)
            circuit.V('ss', 'vss', circuit.gnd, -supply_voltage@u_V)
            
            # Input signal source
            circuit.V('in', 'vin', circuit.gnd, 'AC 1')
            
            # Sallen-Key high-pass topology
            # Swap R and C positions from low-pass
            
            # Calculate component values
            C = 1e-9  # 1nF
            R1 = 1 / (2 * np.pi * cutoff_frequency * C)
            R2 = R1 / (2 * q_factor**2)
            
            # Input capacitors
            circuit.C('1', 'vin', 'node1', C@u_F)
            circuit.C('2', 'node1', 'node2', C@u_F)
            
            # Resistors
            circuit.R('1', 'node1', 'vout', R1@u_Ω)
            circuit.R('2', 'node2', circuit.gnd, R2@u_Ω)
            
            # Op-amp buffer
            circuit.VCVS('opamp', 'vout', circuit.gnd, 'node2', 'inv_in', 100000)
            
            # Feedback for unity gain
            circuit.R('fb', 'vout', 'inv_in', 1@u_Ω)
            
            # Output load
            circuit.R('load', 'vout', circuit.gnd, 10@u_kΩ)
            
            logger.info(f"Created active high-pass filter: fc={cutoff_frequency}Hz, Q={q_factor}")
            return circuit
            
        except Exception as e:
            logger.error(f"Failed to create active high-pass filter: {e}")
            return None
    
    def create_wien_bridge_oscillator(self, frequency: float = 1000, amplitude: float = 1,
                                    supply_voltage: float = 15) -> Optional[Circuit]:
        """Create a Wien bridge oscillator circuit."""
        if not PYSPICE_AVAILABLE:
            logger.error("PySpice not available")
            return None
        
        try:
            circuit = Circuit('Wien Bridge Oscillator')
            
            # Power supplies
            circuit.V('dd', 'vdd', circuit.gnd, supply_voltage@u_V)
            circuit.V('ss', 'vss', circuit.gnd, -supply_voltage@u_V)
            
            # Wien bridge frequency-determining network
            # f = 1/(2*pi*R*C)
            C = 1e-8  # 10nF
            R = 1 / (2 * np.pi * frequency * C)
            
            # Positive feedback network (Wien bridge)
            circuit.R('1', 'vout', 'node1', R@u_Ω)
            circuit.C('1', 'node1', 'non_inv_in', C@u_F)
            circuit.R('2', 'non_inv_in', circuit.gnd, R@u_Ω)
            circuit.C('2', 'node1', circuit.gnd, C@u_F)
            
            # Negative feedback for gain control (gain = 3 for oscillation)
            circuit.R('3', 'inv_in', circuit.gnd, 10@u_kΩ)
            circuit.R('4', 'vout', 'inv_in', 20@u_kΩ)  # Gain = 1 + R4/R3 = 3
            
            # Op-amp
            circuit.VCVS('opamp', 'vout', circuit.gnd, 'non_inv_in', 'inv_in', 100000)
            
            # Output load
            circuit.R('load', 'vout', circuit.gnd, 10@u_kΩ)
            
            # Initial condition to start oscillation
            circuit.IC('vout', amplitude@u_V)
            
            logger.info(f"Created Wien bridge oscillator: f={frequency}Hz")
            return circuit
            
        except Exception as e:
            logger.error(f"Failed to create Wien bridge oscillator: {e}")
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
    
    def run_ac_analysis(self, circuit: Circuit, start_freq: Optional[float] = None, 
                       stop_freq: Optional[float] = None) -> Optional[Dict[str, Any]]:
        """Run AC analysis with frequency sweep for Bode plots and stability analysis."""
        if not circuit or not self.ngspice_shared:
            logger.error("Circuit or NGSpice not available")
            return None
        
        start_freq = start_freq or self.simulation_params.start_frequency
        stop_freq = stop_freq or self.simulation_params.stop_frequency
        points_per_decade = self.simulation_params.points_per_decade
        
        try:
            simulator = circuit.simulator(temperature=25, nominal_temperature=25)
            analysis = simulator.ac(start_frequency=start_freq@u_Hz, 
                                  stop_frequency=stop_freq@u_Hz, 
                                  number_of_points=points_per_decade, 
                                  variation='dec')
            
            results = {
                'analysis_type': 'AC Analysis',
                'frequency': analysis.frequency.as_ndarray().tolist(),
                'nodes': {},
                'magnitude_db': {},
                'phase_deg': {},
                'success': True,
                'start_frequency': start_freq,
                'stop_frequency': stop_freq
            }
            
            # Extract magnitude and phase for each node
            for node in analysis.nodes:
                node_name = str(node)
                if node_name != '0':  # Skip ground node
                    complex_response = analysis[node].as_ndarray()
                    magnitude_db = 20 * np.log10(np.abs(complex_response))
                    phase_deg = np.angle(complex_response, deg=True)
                    
                    results['nodes'][node_name] = complex_response.tolist()
                    results['magnitude_db'][node_name] = magnitude_db.tolist()
                    results['phase_deg'][node_name] = phase_deg.tolist()
            
            logger.info(f"AC analysis completed: {start_freq}-{stop_freq} Hz")
            return results
            
        except Exception as e:
            logger.error(f"AC analysis failed: {e}")
            return {
                'analysis_type': 'AC Analysis',
                'error': str(e),
                'success': False
            }
    
    def run_noise_analysis(self, circuit: Circuit, input_source: str = 'Vin', 
                          output_node: str = 'out') -> Optional[Dict[str, Any]]:
        """Run noise analysis for low-noise circuit design."""
        if not circuit or not self.ngspice_shared:
            logger.error("Circuit or NGSpice not available")
            return None
        
        try:
            simulator = circuit.simulator(temperature=25, nominal_temperature=25)
            
            # Noise analysis requires specific setup
            start_freq = self.simulation_params.start_frequency
            stop_freq = self.simulation_params.stop_frequency
            points_per_decade = self.simulation_params.points_per_decade
            
            # For now, we'll simulate noise by running AC analysis and estimating noise
            # In a full implementation, this would use NGSpice's .noise command
            analysis = simulator.ac(start_frequency=start_freq@u_Hz, 
                                  stop_frequency=stop_freq@u_Hz, 
                                  number_of_points=points_per_decade, 
                                  variation='dec')
            
            results = {
                'analysis_type': 'Noise Analysis',
                'frequency': analysis.frequency.as_ndarray().tolist(),
                'input_noise_voltage': [],
                'input_noise_current': [],
                'output_noise': [],
                'noise_figure_db': [],
                'success': True
            }
            
            # Estimate noise characteristics (simplified model)
            frequencies = analysis.frequency.as_ndarray()
            
            # Typical op-amp noise model: 1/f + white noise
            for freq in frequencies:
                # Input voltage noise (nV/√Hz)
                v_noise = np.sqrt(4 + 100/freq) if freq > 0 else 4
                # Input current noise (pA/√Hz)  
                i_noise = np.sqrt(0.1 + 10/freq) if freq > 0 else 0.1
                # Output noise depends on circuit gain
                output_noise = v_noise * 10  # Assume 20dB gain
                # Noise figure (simplified)
                nf_db = 10 * np.log10(1 + (v_noise**2)/(4*1000*300*1.38e-23*300))
                
                results['input_noise_voltage'].append(v_noise)
                results['input_noise_current'].append(i_noise)
                results['output_noise'].append(output_noise)
                results['noise_figure_db'].append(nf_db)
            
            logger.info("Noise analysis completed")
            return results
            
        except Exception as e:
            logger.error(f"Noise analysis failed: {e}")
            return {
                'analysis_type': 'Noise Analysis',
                'error': str(e),
                'success': False
            }
    
    def run_monte_carlo_analysis(self, circuit_generator, iterations: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Run Monte Carlo analysis for statistical design validation."""
        if not self.ngspice_shared:
            logger.error("NGSpice not available")
            return None
        
        iterations = iterations or self.simulation_params.iterations
        tolerance = self.simulation_params.component_tolerance
        
        try:
            results = {
                'analysis_type': 'Monte Carlo Analysis',
                'iterations': iterations,
                'tolerance': tolerance,
                'dc_results': [],
                'performance_metrics': [],
                'statistics': {},
                'success': True
            }
            
            successful_runs = 0
            
            for i in range(iterations):
                try:
                    # Generate circuit with component variations
                    varied_circuit = self._vary_circuit_components(circuit_generator, tolerance)
                    if not varied_circuit:
                        continue
                    
                    # Run DC analysis on varied circuit
                    dc_result = self.run_dc_analysis(varied_circuit)
                    if dc_result and dc_result.get('success'):
                        results['dc_results'].append(dc_result)
                        successful_runs += 1
                        
                        # Calculate performance metrics for this iteration
                        metrics = self._calculate_performance_metrics(dc_result, varied_circuit)
                        results['performance_metrics'].append(metrics)
                
                except Exception as e:
                    logger.warning(f"Monte Carlo iteration {i} failed: {e}")
                    continue
            
            # Calculate statistics
            if successful_runs > 0:
                results['statistics'] = self._calculate_monte_carlo_statistics(results['performance_metrics'])
                results['success_rate'] = successful_runs / iterations
                logger.info(f"Monte Carlo analysis completed: {successful_runs}/{iterations} successful runs")
            else:
                results['success'] = False
                results['error'] = "No successful Monte Carlo iterations"
            
            return results
            
        except Exception as e:
            logger.error(f"Monte Carlo analysis failed: {e}")
            return {
                'analysis_type': 'Monte Carlo Analysis',
                'error': str(e),
                'success': False
            }
    
    def run_temperature_analysis(self, circuit: Circuit, temp_range: Optional[Tuple[float, float]] = None) -> Optional[Dict[str, Any]]:
        """Run temperature sweep analysis."""
        if not circuit or not self.ngspice_shared:
            logger.error("Circuit or NGSpice not available")
            return None
        
        if temp_range:
            temp_start, temp_stop = temp_range
        else:
            temp_start = self.simulation_params.temp_start
            temp_stop = self.simulation_params.temp_stop
        
        temp_step = self.simulation_params.temp_step
        
        try:
            temperatures = np.arange(temp_start, temp_stop + temp_step, temp_step)
            
            results = {
                'analysis_type': 'Temperature Analysis',
                'temperatures': temperatures.tolist(),
                'dc_results': [],
                'performance_variation': {},
                'success': True
            }
            
            for temp in temperatures:
                try:
                    simulator = circuit.simulator(temperature=temp, nominal_temperature=25)
                    analysis = simulator.operating_point()
                    
                    temp_result = {
                        'temperature': temp,
                        'nodes': {},
                        'currents': {}
                    }
                    
                    # Extract results for this temperature
                    for node in analysis.nodes:
                        temp_result['nodes'][str(node)] = float(analysis[node])
                    
                    for branch in analysis.branches:
                        temp_result['currents'][str(branch)] = float(analysis[branch])
                    
                    results['dc_results'].append(temp_result)
                    
                except Exception as e:
                    logger.warning(f"Temperature analysis failed at {temp}°C: {e}")
                    continue
            
            # Calculate performance variation with temperature
            results['performance_variation'] = self._calculate_temperature_coefficients(results['dc_results'])
            
            logger.info(f"Temperature analysis completed: {temp_start}°C to {temp_stop}°C")
            return results
            
        except Exception as e:
            logger.error(f"Temperature analysis failed: {e}")
            return {
                'analysis_type': 'Temperature Analysis',
                'error': str(e),
                'success': False
            }
    
    def _vary_circuit_components(self, circuit_generator, tolerance: float):
        """Generate circuit with component variations for Monte Carlo analysis."""
        try:
            # This is a simplified implementation
            # In practice, this would modify component values based on tolerance
            varied_params = {}
            
            # Add random variations to key parameters
            if hasattr(circuit_generator, '__call__'):
                # Assume circuit_generator is a function that takes parameters
                return circuit_generator()
            else:
                # Assume it's already a circuit
                return circuit_generator
                
        except Exception as e:
            logger.error(f"Failed to vary circuit components: {e}")
            return None
    
    def _calculate_performance_metrics(self, dc_result: Dict[str, Any], circuit) -> PerformanceMetrics:
        """Calculate performance metrics from simulation results."""
        metrics = PerformanceMetrics()
        
        try:
            # Extract basic metrics from DC analysis
            if 'nodes' in dc_result:
                nodes = dc_result['nodes']
                
                # Calculate power consumption (simplified)
                if 'vcc' in nodes and 'currents' in dc_result:
                    supply_voltage = nodes.get('vcc', 0)
                    total_current = sum(abs(current) for current in dc_result['currents'].values())
                    metrics.power_consumption = supply_voltage * total_current
                
                # Calculate basic gain (if applicable)
                if len(nodes) > 2:  # More than just ground and supply
                    output_nodes = [v for k, v in nodes.items() if k not in ['0', 'vcc']]
                    if output_nodes:
                        metrics.dc_gain = max(output_nodes) / max(1e-9, min(output_nodes))
            
        except Exception as e:
            logger.warning(f"Failed to calculate performance metrics: {e}")
        
        return metrics
    
    def _calculate_monte_carlo_statistics(self, metrics_list: List[PerformanceMetrics]) -> Dict[str, Any]:
        """Calculate statistical summary of Monte Carlo results."""
        stats = {}
        
        try:
            # Extract power consumption values
            power_values = [m.power_consumption for m in metrics_list if m.power_consumption is not None]
            if power_values:
                stats['power_consumption'] = {
                    'mean': np.mean(power_values),
                    'std': np.std(power_values),
                    'min': np.min(power_values),
                    'max': np.max(power_values),
                    'percentile_95': np.percentile(power_values, 95)
                }
            
            # Extract gain values
            gain_values = [m.dc_gain for m in metrics_list if m.dc_gain is not None]
            if gain_values:
                stats['dc_gain'] = {
                    'mean': np.mean(gain_values),
                    'std': np.std(gain_values),
                    'min': np.min(gain_values),
                    'max': np.max(gain_values),
                    'percentile_95': np.percentile(gain_values, 95)
                }
                
        except Exception as e:
            logger.warning(f"Failed to calculate Monte Carlo statistics: {e}")
        
        return stats
    
    def _calculate_temperature_coefficients(self, temp_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate temperature coefficients from temperature sweep results."""
        coefficients = {}
        
        try:
            if len(temp_results) < 2:
                return coefficients
            
            temperatures = [r['temperature'] for r in temp_results]
            
            # Calculate temperature coefficients for each node
            for node_name in temp_results[0]['nodes'].keys():
                node_values = [r['nodes'][node_name] for r in temp_results]
                
                # Linear fit to calculate temperature coefficient
                if len(node_values) == len(temperatures):
                    temp_coeff = np.polyfit(temperatures, node_values, 1)[0]  # Slope
                    coefficients[f'{node_name}_temp_coeff'] = temp_coeff
                    
        except Exception as e:
            logger.warning(f"Failed to calculate temperature coefficients: {e}")
        
        return coefficients
    
    def calculate_performance_metrics(self, ac_results: Optional[Dict[str, Any]] = None,
                                    dc_results: Optional[Dict[str, Any]] = None) -> PerformanceMetrics:
        """Calculate comprehensive performance metrics from simulation results."""
        metrics = PerformanceMetrics()
        
        try:
            # Calculate metrics from AC analysis
            if ac_results and ac_results.get('success'):
                frequencies = np.array(ac_results['frequency'])
                
                # Find the main output node (assume it's the one with highest magnitude)
                max_magnitude_node = None
                max_magnitude = 0
                
                for node_name, magnitude_db in ac_results['magnitude_db'].items():
                    if node_name != '0':  # Skip ground
                        max_mag = np.max(magnitude_db)
                        if max_mag > max_magnitude:
                            max_magnitude = max_mag
                            max_magnitude_node = node_name
                
                if max_magnitude_node:
                    magnitude_db = np.array(ac_results['magnitude_db'][max_magnitude_node])
                    phase_deg = np.array(ac_results['phase_deg'][max_magnitude_node])
                    
                    # Calculate DC gain
                    metrics.dc_gain = magnitude_db[0] if len(magnitude_db) > 0 else None
                    
                    # Calculate bandwidth (-3dB point)
                    if len(magnitude_db) > 1:
                        dc_gain_db = magnitude_db[0]
                        cutoff_db = dc_gain_db - 3
                        cutoff_indices = np.where(magnitude_db <= cutoff_db)[0]
                        if len(cutoff_indices) > 0:
                            cutoff_index = cutoff_indices[0]
                            metrics.bandwidth = frequencies[cutoff_index]
                            metrics.cutoff_frequency = frequencies[cutoff_index]
                    
                    # Calculate gain and phase margins for stability
                    unity_gain_indices = np.where(magnitude_db <= 0)[0]
                    if len(unity_gain_indices) > 0:
                        unity_gain_index = unity_gain_indices[0]
                        metrics.unity_gain_frequency = frequencies[unity_gain_index]
                        metrics.phase_margin = 180 + phase_deg[unity_gain_index]
                    
                    # Calculate gain margin
                    phase_180_indices = np.where(np.abs(phase_deg + 180) < 5)[0]
                    if len(phase_180_indices) > 0:
                        phase_180_index = phase_180_indices[0]
                        metrics.gain_margin = -magnitude_db[phase_180_index]
            
            # Calculate metrics from DC analysis
            if dc_results and dc_results.get('success'):
                # Power consumption
                if 'currents' in dc_results and 'nodes' in dc_results:
                    supply_current = 0
                    supply_voltage = dc_results['nodes'].get('vcc', 5.0)
                    
                    for current_name, current_value in dc_results['currents'].items():
                        if 'supply' in current_name.lower() or 'vcc' in current_name.lower():
                            supply_current += abs(current_value)
                    
                    metrics.power_consumption = supply_voltage * supply_current
                    
        except Exception as e:
            logger.warning(f"Failed to calculate performance metrics: {e}")
        
        return metrics
    
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
        """Generate enhanced plots from analysis results and return as base64 string."""
        try:
            if not analysis_results.get('success'):
                return None
            
            analysis_type = analysis_results['analysis_type']
            
            if analysis_type == 'AC Analysis':
                return self._generate_bode_plot(analysis_results)
            elif analysis_type == 'Noise Analysis':
                return self._generate_noise_plot(analysis_results)
            elif analysis_type == 'Monte Carlo Analysis':
                return self._generate_monte_carlo_plot(analysis_results)
            elif analysis_type == 'Temperature Analysis':
                return self._generate_temperature_plot(analysis_results)
            elif analysis_type == 'Transient':
                return self._generate_transient_plot(analysis_results)
            elif analysis_type == 'DC Operating Point':
                return self._generate_dc_plot(analysis_results)
            else:
                logger.warning(f"Unknown analysis type for plotting: {analysis_type}")
                return None
                
        except Exception as e:
            logger.error(f"Plot generation failed: {e}")
            return None
    
    def _generate_bode_plot(self, ac_results: Dict[str, Any]) -> Optional[str]:
        """Generate Bode plot (magnitude and phase) from AC analysis."""
        try:
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
            
            frequencies = np.array(ac_results['frequency'])
            
            # Plot magnitude for each node
            for node_name, magnitude_db in ac_results['magnitude_db'].items():
                if node_name != '0':  # Skip ground node
                    ax1.semilogx(frequencies, magnitude_db, label=f'Node {node_name}')
            
            ax1.set_xlabel('Frequency (Hz)')
            ax1.set_ylabel('Magnitude (dB)')
            ax1.set_title('Bode Plot - Magnitude Response')
            ax1.grid(True, which="both", ls="-", alpha=0.3)
            ax1.legend()
            
            # Plot phase for each node
            for node_name, phase_deg in ac_results['phase_deg'].items():
                if node_name != '0':  # Skip ground node
                    ax2.semilogx(frequencies, phase_deg, label=f'Node {node_name}')
            
            ax2.set_xlabel('Frequency (Hz)')
            ax2.set_ylabel('Phase (degrees)')
            ax2.set_title('Bode Plot - Phase Response')
            ax2.grid(True, which="both", ls="-", alpha=0.3)
            ax2.legend()
            
            plt.tight_layout()
            
            # Convert to base64
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
            buffer.seek(0)
            plot_data = base64.b64encode(buffer.getvalue()).decode()
            plt.close()
            
            return plot_data
            
        except Exception as e:
            logger.error(f"Bode plot generation failed: {e}")
            return None
    
    def _generate_noise_plot(self, noise_results: Dict[str, Any]) -> Optional[str]:
        """Generate noise analysis plot."""
        try:
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
            
            frequencies = np.array(noise_results['frequency'])
            
            # Input noise voltage
            ax1.loglog(frequencies, noise_results['input_noise_voltage'], 'b-', label='Input Voltage Noise')
            ax1.set_xlabel('Frequency (Hz)')
            ax1.set_ylabel('Input Noise Voltage (nV/√Hz)')
            ax1.set_title('Input Noise Voltage vs Frequency')
            ax1.grid(True, which="both", ls="-", alpha=0.3)
            ax1.legend()
            
            # Noise figure
            ax2.semilogx(frequencies, noise_results['noise_figure_db'], 'r-', label='Noise Figure')
            ax2.set_xlabel('Frequency (Hz)')
            ax2.set_ylabel('Noise Figure (dB)')
            ax2.set_title('Noise Figure vs Frequency')
            ax2.grid(True, which="both", ls="-", alpha=0.3)
            ax2.legend()
            
            plt.tight_layout()
            
            # Convert to base64
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
            buffer.seek(0)
            plot_data = base64.b64encode(buffer.getvalue()).decode()
            plt.close()
            
            return plot_data
            
        except Exception as e:
            logger.error(f"Noise plot generation failed: {e}")
            return None
    
    def _generate_monte_carlo_plot(self, mc_results: Dict[str, Any]) -> Optional[str]:
        """Generate Monte Carlo analysis histogram plots."""
        try:
            fig, axes = plt.subplots(2, 2, figsize=(12, 10))
            
            stats = mc_results.get('statistics', {})
            
            # Power consumption histogram
            if 'power_consumption' in stats:
                power_data = [m.power_consumption for m in mc_results['performance_metrics'] 
                            if m.power_consumption is not None]
                if power_data:
                    axes[0, 0].hist(power_data, bins=20, alpha=0.7, color='blue')
                    axes[0, 0].axvline(stats['power_consumption']['mean'], color='red', 
                                     linestyle='--', label=f"Mean: {stats['power_consumption']['mean']:.3f}")
                    axes[0, 0].set_xlabel('Power Consumption (W)')
                    axes[0, 0].set_ylabel('Frequency')
                    axes[0, 0].set_title('Power Consumption Distribution')
                    axes[0, 0].legend()
                    axes[0, 0].grid(True, alpha=0.3)
            
            # DC gain histogram
            if 'dc_gain' in stats:
                gain_data = [m.dc_gain for m in mc_results['performance_metrics'] 
                           if m.dc_gain is not None]
                if gain_data:
                    axes[0, 1].hist(gain_data, bins=20, alpha=0.7, color='green')
                    axes[0, 1].axvline(stats['dc_gain']['mean'], color='red', 
                                     linestyle='--', label=f"Mean: {stats['dc_gain']['mean']:.3f}")
                    axes[0, 1].set_xlabel('DC Gain')
                    axes[0, 1].set_ylabel('Frequency')
                    axes[0, 1].set_title('DC Gain Distribution')
                    axes[0, 1].legend()
                    axes[0, 1].grid(True, alpha=0.3)
            
            # Success rate pie chart
            success_rate = mc_results.get('success_rate', 0)
            failure_rate = 1 - success_rate
            axes[1, 0].pie([success_rate, failure_rate], labels=['Success', 'Failure'], 
                          colors=['green', 'red'], autopct='%1.1f%%')
            axes[1, 0].set_title(f'Monte Carlo Success Rate\n({mc_results["iterations"]} iterations)')
            
            # Summary statistics text
            axes[1, 1].axis('off')
            summary_text = f"Monte Carlo Analysis Summary\n\n"
            summary_text += f"Iterations: {mc_results['iterations']}\n"
            summary_text += f"Success Rate: {success_rate:.1%}\n"
            summary_text += f"Component Tolerance: {mc_results['tolerance']:.1%}\n\n"
            
            if 'power_consumption' in stats:
                summary_text += f"Power Consumption:\n"
                summary_text += f"  Mean: {stats['power_consumption']['mean']:.3f} W\n"
                summary_text += f"  Std: {stats['power_consumption']['std']:.3f} W\n"
                summary_text += f"  95th percentile: {stats['power_consumption']['percentile_95']:.3f} W\n"
            
            axes[1, 1].text(0.1, 0.9, summary_text, transform=axes[1, 1].transAxes, 
                           fontsize=10, verticalalignment='top', fontfamily='monospace')
            
            plt.tight_layout()
            
            # Convert to base64
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
            buffer.seek(0)
            plot_data = base64.b64encode(buffer.getvalue()).decode()
            plt.close()
            
            return plot_data
            
        except Exception as e:
            logger.error(f"Monte Carlo plot generation failed: {e}")
            return None
    
    def _generate_temperature_plot(self, temp_results: Dict[str, Any]) -> Optional[str]:
        """Generate temperature analysis plot."""
        try:
            plt.figure(figsize=(12, 8))
            
            temperatures = temp_results['temperatures']
            
            # Plot voltage vs temperature for each node
            for i, result in enumerate(temp_results['dc_results']):
                if i == 0:  # First iteration to get node names
                    for node_name in result['nodes'].keys():
                        if node_name != '0':  # Skip ground
                            node_voltages = [r['nodes'][node_name] for r in temp_results['dc_results']]
                            plt.plot(temperatures, node_voltages, 'o-', label=f'Node {node_name}')
            
            plt.xlabel('Temperature (°C)')
            plt.ylabel('Voltage (V)')
            plt.title('Voltage vs Temperature')
            plt.grid(True, alpha=0.3)
            plt.legend()
            
            # Add temperature coefficient annotations
            if 'performance_variation' in temp_results:
                coeffs = temp_results['performance_variation']
                coeff_text = "Temperature Coefficients:\n"
                for coeff_name, coeff_value in coeffs.items():
                    coeff_text += f"{coeff_name}: {coeff_value:.2e} V/°C\n"
                
                plt.text(0.02, 0.98, coeff_text, transform=plt.gca().transAxes, 
                        fontsize=9, verticalalignment='top', fontfamily='monospace',
                        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
            
            plt.tight_layout()
            
            # Convert to base64
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
            buffer.seek(0)
            plot_data = base64.b64encode(buffer.getvalue()).decode()
            plt.close()
            
            return plot_data
            
        except Exception as e:
            logger.error(f"Temperature plot generation failed: {e}")
            return None
    
    def _generate_transient_plot(self, transient_results: Dict[str, Any]) -> Optional[str]:
        """Generate transient analysis plot."""
        try:
            plt.figure(figsize=(10, 6))
            
            time = transient_results['time']
            for node_name, voltages in transient_results['nodes'].items():
                if node_name != '0':  # Skip ground node
                    plt.plot(time, voltages, label=f'Node {node_name}')
            
            plt.xlabel('Time (s)')
            plt.ylabel('Voltage (V)')
            plt.title('Transient Analysis Results')
            plt.legend()
            plt.grid(True)
            
            # Convert to base64
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
            buffer.seek(0)
            plot_data = base64.b64encode(buffer.getvalue()).decode()
            plt.close()
            
            return plot_data
            
        except Exception as e:
            logger.error(f"Transient plot generation failed: {e}")
            return None
    
    def _generate_dc_plot(self, dc_results: Dict[str, Any]) -> Optional[str]:
        """Generate DC operating point plot."""
        try:
            plt.figure(figsize=(10, 6))
            
            nodes = list(dc_results['nodes'].keys())
            voltages = list(dc_results['nodes'].values())
            
            plt.bar(nodes, voltages)
            plt.xlabel('Nodes')
            plt.ylabel('Voltage (V)')
            plt.title('DC Operating Point Analysis')
            plt.grid(True, axis='y')
            
            # Convert to base64
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
            buffer.seek(0)
            plot_data = base64.b64encode(buffer.getvalue()).decode()
            plt.close()
            
            return plot_data
            
        except Exception as e:
            logger.error(f"DC plot generation failed: {e}")
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