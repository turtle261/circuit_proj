#!/usr/bin/env python3
"""
Test Phase 2.1 integration with CrewAI agents.
"""

import os
import sys
import json
import logging

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.tools.advanced_simulation_tool import AdvancedSimulationTool, CircuitValidationTool

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_advanced_simulation_tool():
    """Test the advanced simulation tool directly."""
    logger.info("Testing Advanced Simulation Tool...")
    
    tool = AdvancedSimulationTool()
    
    # Test LED circuit with multiple analyses
    test_input = {
        "circuit_type": "led",
        "parameters": {
            "led_voltage": 2.0,
            "supply_voltage": 5.0,
            "start_frequency": 1,
            "stop_frequency": 1000,
            "monte_carlo_iterations": 10,
            "temperature_range": [0, 50]
        },
        "analysis_types": ["dc", "ac", "noise", "monte_carlo", "temperature"],
        "simulation_params": {
            "start_frequency": 1.0,
            "stop_frequency": 1000.0,
            "points_per_decade": 20,
            "iterations": 10,
            "component_tolerance": 0.05
        }
    }
    
    result = tool._run(json.dumps(test_input))
    result_data = json.loads(result)
    
    logger.info(f"Simulation success: {result_data.get('success')}")
    logger.info(f"Analyses completed: {list(result_data.get('analyses', {}).keys())}")
    logger.info(f"Plots generated: {list(result_data.get('plots', {}).keys())}")
    
    # Check performance metrics
    metrics = result_data.get('performance_metrics', {})
    if metrics:
        logger.info("Performance Metrics:")
        for key, value in metrics.items():
            if value is not None:
                logger.info(f"  {key}: {value}")
    
    # Check recommendations
    recommendations = result_data.get('recommendations', [])
    logger.info(f"Recommendations: {len(recommendations)}")
    for rec in recommendations:
        logger.info(f"  - {rec}")
    
    return result_data.get('success', False)

def test_circuit_validation_tool():
    """Test the circuit validation tool."""
    logger.info("Testing Circuit Validation Tool...")
    
    # First run simulation
    sim_tool = AdvancedSimulationTool()
    sim_input = {
        "circuit_type": "led",
        "parameters": {"led_voltage": 2.0, "supply_voltage": 5.0},
        "analysis_types": ["dc", "ac", "noise"]
    }
    
    sim_result = sim_tool._run(json.dumps(sim_input))
    sim_data = json.loads(sim_result)
    
    # Now validate against requirements
    validation_tool = CircuitValidationTool()
    validation_input = {
        "simulation_results": sim_data,
        "requirements": {
            "max_power": 0.1,
            "min_gain": -10,
            "max_noise": 10,
            "min_bandwidth": 100,
            "temperature_range": [-40, 85],
            "supply_voltage": 5.0
        }
    }
    
    validation_result = validation_tool._run(json.dumps(validation_input))
    validation_data = json.loads(validation_result)
    
    logger.info(f"Validation overall pass: {validation_data.get('overall_pass')}")
    
    checks = validation_data.get('checks', {})
    for check_name, check_data in checks.items():
        status = "✓" if check_data['passed'] else "✗"
        logger.info(f"  {check_name}: {status} {check_data['actual']} (req: {check_data['requirement']})")
    
    violations = validation_data.get('violations', [])
    if violations:
        logger.info("Violations:")
        for violation in violations:
            logger.info(f"  - {violation}")
    
    return validation_data.get('overall_pass', False)

def test_opamp_circuit():
    """Test op-amp circuit simulation."""
    logger.info("Testing Op-Amp Circuit Simulation...")
    
    tool = AdvancedSimulationTool()
    
    test_input = {
        "circuit_type": "opamp_inverting",
        "parameters": {
            "gain": -10,
            "input_impedance": 10000,
            "supply_voltage": 15,
            "start_frequency": 1,
            "stop_frequency": 100000
        },
        "analysis_types": ["dc", "ac"],
        "simulation_params": {
            "start_frequency": 1.0,
            "stop_frequency": 100000.0,
            "points_per_decade": 50
        }
    }
    
    result = tool._run(json.dumps(test_input))
    result_data = json.loads(result)
    
    logger.info(f"Op-amp simulation success: {result_data.get('success')}")
    
    if result_data.get('success'):
        metrics = result_data.get('performance_metrics', {})
        if metrics.get('dc_gain'):
            logger.info(f"DC Gain: {metrics['dc_gain']:.1f} dB")
        if metrics.get('bandwidth'):
            logger.info(f"Bandwidth: {metrics['bandwidth']:.1f} Hz")
    
    return result_data.get('success', False)

def main():
    """Run Phase 2.1 integration tests."""
    logger.info("Phase 2.1 CrewAI Integration Test Suite")
    logger.info("=" * 50)
    
    tests = [
        ("Advanced Simulation Tool", test_advanced_simulation_tool),
        ("Circuit Validation Tool", test_circuit_validation_tool),
        ("Op-Amp Circuit Test", test_opamp_circuit)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\nRunning: {test_name}")
        logger.info("-" * 30)
        
        try:
            result = test_func()
            if result:
                logger.info(f"✓ {test_name}: PASSED")
                passed += 1
            else:
                logger.info(f"✗ {test_name}: FAILED")
        except Exception as e:
            logger.error(f"✗ {test_name}: ERROR - {e}")
    
    logger.info("\n" + "=" * 50)
    logger.info(f"Integration Test Results: {passed}/{total} passed")
    
    if passed == total:
        logger.info("🎉 Phase 2.1 integration is fully functional!")
        return True
    else:
        logger.warning("⚠️ Some integration tests failed.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)