"""
Advanced simulation tool for Phase 2.1 capabilities.
Integrates enhanced SPICE simulator with CrewAI agents.
"""

import json
import logging
from typing import Dict, Any, Optional, List
from crewai.tools import BaseTool

# Import enhanced simulator
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from simulations.spice_simulator import (
    SpiceSimulator, SimulationParameters, PerformanceMetrics, 
    CircuitType, PYSPICE_AVAILABLE
)

logger = logging.getLogger(__name__)

class AdvancedSimulationTool(BaseTool):
    """Advanced simulation tool with Phase 2.1 capabilities."""
    
    name: str = "Advanced Circuit Simulator"
    description: str = """
    Perform comprehensive circuit simulation with advanced analysis capabilities:
    - DC operating point analysis
    - Transient analysis for time-domain behavior
    - AC analysis with frequency sweeps (Bode plots)
    - Noise analysis for low-noise design
    - Monte Carlo analysis for statistical validation
    - Temperature analysis for thermal performance
    - Performance metrics calculation (gain, bandwidth, stability margins)
    - Advanced plotting and visualization
    
    Input should be a simple JSON string like:
    {"circuit_type": "led", "analysis_types": ["dc", "transient"]}
    
    Supported circuit types: led, opamp_inverting, opamp_non_inverting, lowpass_filter, highpass_filter, wien_oscillator
    Supported analysis types: dc, transient, ac, noise, monte_carlo, temperature
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._simulator = None
    
    @property
    def simulator(self):
        if self._simulator is None:
            self._simulator = SpiceSimulator()
        return self._simulator
        
    def _run(self, input_data: str) -> str:
        """Run advanced circuit simulation."""
        try:
            # Parse input - handle both string and dict inputs
            if isinstance(input_data, str):
                try:
                    data = json.loads(input_data)
                except json.JSONDecodeError as e:
                    logger.error(f"JSON parsing error: {e}")
                    # Try to extract basic info for fallback
                    data = {
                        'circuit_type': 'led',
                        'parameters': {},
                        'analysis_types': ['dc', 'transient'],
                        'simulation_params': {}
                    }
            else:
                data = input_data
                
            circuit_type = data.get('circuit_type', 'led')
            parameters = data.get('parameters', {})
            analysis_types = data.get('analysis_types', ['dc', 'transient'])
            sim_params = data.get('simulation_params', {})
            
            # Set simulation parameters if provided
            if sim_params:
                params = SimulationParameters(**sim_params)
                self.simulator.set_simulation_parameters(params)
            
            # Create circuit based on type
            circuit = self._create_circuit(circuit_type, parameters)
            if not circuit:
                return json.dumps({
                    "success": False,
                    "error": f"Failed to create {circuit_type} circuit",
                    "fallback_used": not PYSPICE_AVAILABLE
                })
            
            # Run requested analyses
            results = {
                "success": True,
                "circuit_type": circuit_type,
                "parameters": parameters,
                "analyses": {}
            }
            
            # DC Analysis
            if 'dc' in analysis_types:
                dc_results = self.simulator.run_dc_analysis(circuit)
                if dc_results:
                    results["analyses"]["dc"] = dc_results
            
            # Transient Analysis
            if 'transient' in analysis_types:
                duration = parameters.get('transient_duration', 0.001)
                transient_results = self.simulator.run_transient_analysis(circuit, duration)
                if transient_results:
                    results["analyses"]["transient"] = transient_results
            
            # AC Analysis (Phase 2.1)
            if 'ac' in analysis_types:
                start_freq = parameters.get('start_frequency', 1)
                stop_freq = parameters.get('stop_frequency', 10000)
                ac_results = self.simulator.run_ac_analysis(circuit, start_freq, stop_freq)
                if ac_results:
                    results["analyses"]["ac"] = ac_results
            
            # Noise Analysis (Phase 2.1)
            if 'noise' in analysis_types:
                noise_results = self.simulator.run_noise_analysis(circuit)
                if noise_results:
                    results["analyses"]["noise"] = noise_results
            
            # Monte Carlo Analysis (Phase 2.1)
            if 'monte_carlo' in analysis_types:
                iterations = parameters.get('monte_carlo_iterations', 50)
                circuit_generator = lambda: self._create_circuit(circuit_type, parameters)
                mc_results = self.simulator.run_monte_carlo_analysis(circuit_generator, iterations)
                if mc_results:
                    results["analyses"]["monte_carlo"] = mc_results
            
            # Temperature Analysis (Phase 2.1)
            if 'temperature' in analysis_types:
                temp_range = parameters.get('temperature_range', (-40, 85))
                temp_results = self.simulator.run_temperature_analysis(circuit, temp_range)
                if temp_results:
                    results["analyses"]["temperature"] = temp_results
            
            # Calculate comprehensive performance metrics
            ac_data = results["analyses"].get("ac")
            dc_data = results["analyses"].get("dc")
            
            if ac_data or dc_data:
                metrics = self.simulator.calculate_performance_metrics(ac_data, dc_data)
                results["performance_metrics"] = {
                    "dc_gain": metrics.dc_gain,
                    "bandwidth": metrics.bandwidth,
                    "cutoff_frequency": metrics.cutoff_frequency,
                    "phase_margin": metrics.phase_margin,
                    "gain_margin": metrics.gain_margin,
                    "unity_gain_frequency": metrics.unity_gain_frequency,
                    "power_consumption": metrics.power_consumption,
                    "input_impedance": metrics.input_impedance,
                    "output_impedance": metrics.output_impedance,
                    "slew_rate": metrics.slew_rate,
                    "settling_time": metrics.settling_time,
                    "thd": metrics.thd,
                    "snr": metrics.snr
                }
            
            # Generate plots for each analysis
            plots = {}
            for analysis_name, analysis_data in results["analyses"].items():
                if analysis_data and analysis_data.get('success'):
                    plot = self.simulator.generate_plot(analysis_data)
                    if plot:
                        plots[f"{analysis_name}_plot"] = plot
            
            results["plots"] = plots
            
            # Add recommendations based on results
            results["recommendations"] = self._generate_recommendations(results)
            
            # Convert complex numbers and numpy types to serializable format
            import numpy as np
            from dataclasses import asdict, is_dataclass
            def convert_complex(obj):
                if isinstance(obj, complex):
                    return {"real": obj.real, "imag": obj.imag}
                elif isinstance(obj, (np.integer, np.floating)):
                    return float(obj)
                elif isinstance(obj, np.ndarray):
                    return obj.tolist()
                elif is_dataclass(obj):
                    return asdict(obj)
                elif isinstance(obj, dict):
                    return {k: convert_complex(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_complex(item) for item in obj]
                else:
                    return obj
            
            serializable_results = convert_complex(results)
            return json.dumps(serializable_results, indent=2)
            
        except Exception as e:
            logger.error(f"Advanced simulation failed: {e}")
            return json.dumps({
                "success": False,
                "error": str(e),
                "fallback_available": True
            })
    
    def _create_circuit(self, circuit_type: str, parameters: Dict[str, Any]):
        """Create circuit based on type and parameters."""
        try:
            if circuit_type == 'led':
                led_voltage = parameters.get('led_voltage', 2.0)
                supply_voltage = parameters.get('supply_voltage', 5.0)
                return self.simulator.create_led_circuit(led_voltage, supply_voltage)
            
            elif circuit_type == 'opamp_inverting':
                gain = parameters.get('gain', -10)
                input_impedance = parameters.get('input_impedance', 10000)
                supply_voltage = parameters.get('supply_voltage', 15)
                return self.simulator.create_opamp_inverting_amplifier(gain, input_impedance, supply_voltage)
            
            elif circuit_type == 'opamp_non_inverting':
                gain = parameters.get('gain', 10)
                input_impedance = parameters.get('input_impedance', 1e6)
                supply_voltage = parameters.get('supply_voltage', 15)
                return self.simulator.create_opamp_non_inverting_amplifier(gain, input_impedance, supply_voltage)
            
            elif circuit_type == 'lowpass_filter':
                cutoff_frequency = parameters.get('cutoff_frequency', 1000)
                gain = parameters.get('gain', 1)
                q_factor = parameters.get('q_factor', 0.707)
                supply_voltage = parameters.get('supply_voltage', 15)
                return self.simulator.create_active_lowpass_filter(cutoff_frequency, gain, q_factor, supply_voltage)
            
            elif circuit_type == 'highpass_filter':
                cutoff_frequency = parameters.get('cutoff_frequency', 1000)
                gain = parameters.get('gain', 1)
                q_factor = parameters.get('q_factor', 0.707)
                supply_voltage = parameters.get('supply_voltage', 15)
                return self.simulator.create_active_highpass_filter(cutoff_frequency, gain, q_factor, supply_voltage)
            
            elif circuit_type == 'wien_oscillator':
                frequency = parameters.get('frequency', 1000)
                amplitude = parameters.get('amplitude', 1)
                supply_voltage = parameters.get('supply_voltage', 15)
                return self.simulator.create_wien_bridge_oscillator(frequency, amplitude, supply_voltage)
            
            else:
                logger.warning(f"Unknown circuit type: {circuit_type}")
                return None
                
        except Exception as e:
            logger.error(f"Circuit creation failed: {e}")
            return None
    
    def _generate_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """Generate design recommendations based on simulation results."""
        recommendations = []
        
        try:
            # Check performance metrics
            metrics = results.get("performance_metrics", {})
            
            # Power consumption recommendations
            power = metrics.get("power_consumption")
            if power and power > 0.1:  # > 100mW
                recommendations.append("Consider reducing power consumption - current draw is high")
            
            # Stability recommendations
            phase_margin = metrics.get("phase_margin")
            if phase_margin and phase_margin < 45:
                recommendations.append("Phase margin is low - consider compensation for stability")
            
            gain_margin = metrics.get("gain_margin")
            if gain_margin and gain_margin < 6:
                recommendations.append("Gain margin is low - circuit may be unstable")
            
            # Bandwidth recommendations
            bandwidth = metrics.get("bandwidth")
            cutoff_freq = metrics.get("cutoff_frequency")
            if bandwidth and cutoff_freq and bandwidth < cutoff_freq * 0.1:
                recommendations.append("Bandwidth is limited - consider higher speed op-amps")
            
            # Noise recommendations
            noise_analysis = results.get("analyses", {}).get("noise")
            if noise_analysis and noise_analysis.get("success"):
                avg_noise = sum(noise_analysis["input_noise_voltage"]) / len(noise_analysis["input_noise_voltage"])
                if avg_noise > 10:  # > 10 nV/√Hz
                    recommendations.append("Input noise is high - consider low-noise op-amps")
            
            # Monte Carlo recommendations
            mc_analysis = results.get("analyses", {}).get("monte_carlo")
            if mc_analysis and mc_analysis.get("success"):
                success_rate = mc_analysis.get("success_rate", 1.0)
                if success_rate < 0.95:
                    recommendations.append("Monte Carlo success rate is low - design may be sensitive to component variations")
            
            # Temperature recommendations
            temp_analysis = results.get("analyses", {}).get("temperature")
            if temp_analysis and temp_analysis.get("success"):
                temp_coeffs = temp_analysis.get("performance_variation", {})
                for coeff_name, coeff_value in temp_coeffs.items():
                    if abs(coeff_value) > 1e-3:  # > 1mV/°C
                        recommendations.append(f"High temperature coefficient for {coeff_name} - consider temperature compensation")
            
            if not recommendations:
                recommendations.append("Circuit design meets all performance criteria")
                
        except Exception as e:
            logger.warning(f"Failed to generate recommendations: {e}")
            recommendations.append("Unable to generate specific recommendations - review simulation results manually")
        
        return recommendations

class CircuitValidationTool(BaseTool):
    """Tool for validating circuit designs against requirements."""
    
    name: str = "Circuit Validator"
    description: str = """
    Validate circuit design against specified requirements.
    
    Input should be a JSON string with:
    {
        "simulation_results": {simulation results from AdvancedSimulationTool},
        "requirements": {
            "max_power": 0.1,
            "min_gain": 10,
            "max_noise": 5,
            "min_bandwidth": 1000,
            "temperature_range": [-40, 85],
            "supply_voltage": 5.0
        }
    }
    """
    
    def _run(self, input_data: str) -> str:
        """Validate circuit against requirements."""
        try:
            data = json.loads(input_data)
            sim_results = data.get('simulation_results', {})
            requirements = data.get('requirements', {})
            
            validation_results = {
                "overall_pass": True,
                "checks": {},
                "violations": [],
                "recommendations": []
            }
            
            metrics = sim_results.get("performance_metrics", {})
            
            # Power consumption check
            if "max_power" in requirements:
                power = metrics.get("power_consumption")
                if power is not None:
                    passed = power <= requirements["max_power"]
                    validation_results["checks"]["power_consumption"] = {
                        "requirement": f"≤ {requirements['max_power']} W",
                        "actual": f"{power:.3f} W",
                        "passed": passed
                    }
                    if not passed:
                        validation_results["overall_pass"] = False
                        validation_results["violations"].append(f"Power consumption {power:.3f}W exceeds limit {requirements['max_power']}W")
            
            # Gain check
            if "min_gain" in requirements:
                gain = metrics.get("dc_gain")
                if gain is not None:
                    passed = gain >= requirements["min_gain"]
                    validation_results["checks"]["dc_gain"] = {
                        "requirement": f"≥ {requirements['min_gain']} dB",
                        "actual": f"{gain:.1f} dB",
                        "passed": passed
                    }
                    if not passed:
                        validation_results["overall_pass"] = False
                        validation_results["violations"].append(f"DC gain {gain:.1f}dB below minimum {requirements['min_gain']}dB")
            
            # Noise check
            if "max_noise" in requirements:
                noise_analysis = sim_results.get("analyses", {}).get("noise")
                if noise_analysis and noise_analysis.get("success"):
                    avg_noise = sum(noise_analysis["input_noise_voltage"]) / len(noise_analysis["input_noise_voltage"])
                    passed = avg_noise <= requirements["max_noise"]
                    validation_results["checks"]["input_noise"] = {
                        "requirement": f"≤ {requirements['max_noise']} nV/√Hz",
                        "actual": f"{avg_noise:.2f} nV/√Hz",
                        "passed": passed
                    }
                    if not passed:
                        validation_results["overall_pass"] = False
                        validation_results["violations"].append(f"Input noise {avg_noise:.2f}nV/√Hz exceeds limit {requirements['max_noise']}nV/√Hz")
            
            # Bandwidth check
            if "min_bandwidth" in requirements:
                bandwidth = metrics.get("bandwidth")
                if bandwidth is not None:
                    passed = bandwidth >= requirements["min_bandwidth"]
                    validation_results["checks"]["bandwidth"] = {
                        "requirement": f"≥ {requirements['min_bandwidth']} Hz",
                        "actual": f"{bandwidth:.1f} Hz",
                        "passed": passed
                    }
                    if not passed:
                        validation_results["overall_pass"] = False
                        validation_results["violations"].append(f"Bandwidth {bandwidth:.1f}Hz below minimum {requirements['min_bandwidth']}Hz")
            
            # Temperature range check
            if "temperature_range" in requirements:
                temp_analysis = sim_results.get("analyses", {}).get("temperature")
                if temp_analysis and temp_analysis.get("success"):
                    temp_range = temp_analysis.get("temperatures", [])
                    req_range = requirements["temperature_range"]
                    if temp_range:
                        min_temp, max_temp = min(temp_range), max(temp_range)
                        passed = min_temp <= req_range[0] and max_temp >= req_range[1]
                        validation_results["checks"]["temperature_range"] = {
                            "requirement": f"{req_range[0]}°C to {req_range[1]}°C",
                            "actual": f"{min_temp}°C to {max_temp}°C",
                            "passed": passed
                        }
                        if not passed:
                            validation_results["overall_pass"] = False
                            validation_results["violations"].append(f"Temperature range {min_temp}°C to {max_temp}°C doesn't cover required {req_range[0]}°C to {req_range[1]}°C")
            
            # Generate recommendations
            if validation_results["violations"]:
                validation_results["recommendations"].extend([
                    "Review circuit design to address requirement violations",
                    "Consider component selection optimization",
                    "Evaluate circuit topology alternatives"
                ])
            else:
                validation_results["recommendations"].append("Circuit design meets all specified requirements")
            
            return json.dumps(validation_results, indent=2)
            
        except Exception as e:
            logger.error(f"Circuit validation failed: {e}")
            return json.dumps({
                "overall_pass": False,
                "error": str(e),
                "recommendations": ["Manual validation required due to tool error"]
            })