"""
Component selection module with Thompson Sampling algorithm.
"""
import logging
import json
import random
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from database.models import Component, ComponentPerformance, get_session

logger = logging.getLogger(__name__)

class ThompsonSamplingSelector:
    """Component selection using Thompson Sampling algorithm."""
    
    def __init__(self):
        self.session = get_session()
        
    def select_resistor_for_led(self, supply_voltage: float, led_voltage: float, 
                              target_current: float) -> Dict[str, Any]:
        """Select optimal resistor for LED circuit using Thompson Sampling."""
        try:
            # Calculate ideal resistance
            ideal_resistance = (supply_voltage - led_voltage) / target_current
            
            # Get available resistors from database
            resistors = self.session.query(Component).filter(
                Component.category == 'resistor'
            ).all()
            
            if not resistors:
                # Fallback to calculated value
                return self._create_fallback_resistor(ideal_resistance)
            
            # Calculate scores for each resistor using Thompson Sampling
            resistor_scores = []
            for resistor in resistors:
                score = self._calculate_thompson_score(resistor, 'led_circuit', ideal_resistance)
                resistor_scores.append((resistor, score))
            
            # Select best resistor
            best_resistor, best_score = max(resistor_scores, key=lambda x: x[1])
            
            # Calculate actual performance
            actual_resistance = float(best_resistor.value)
            actual_current = (supply_voltage - led_voltage) / actual_resistance
            power_dissipation = actual_current ** 2 * actual_resistance
            
            return {
                'component': {
                    'id': best_resistor.id,
                    'name': best_resistor.name,
                    'value': best_resistor.value,
                    'unit': best_resistor.unit,
                    'power_rating': best_resistor.power_rating,
                    'cost': best_resistor.cost
                },
                'performance': {
                    'ideal_resistance': ideal_resistance,
                    'actual_resistance': actual_resistance,
                    'target_current': target_current,
                    'actual_current': actual_current,
                    'power_dissipation': power_dissipation,
                    'efficiency_score': best_score
                },
                'selection_method': 'thompson_sampling'
            }
            
        except Exception as e:
            logger.error(f"Resistor selection failed: {e}")
            return self._create_fallback_resistor(ideal_resistance)
    
    def select_led(self, color: str = 'red', max_current: float = 0.02) -> Dict[str, Any]:
        """Select LED component."""
        try:
            # Get available LEDs from database
            leds = self.session.query(Component).filter(
                Component.category == 'led'
            ).all()
            
            if not leds:
                return self._create_fallback_led(color)
            
            # Filter by color preference if specified
            color_filtered = [led for led in leds if color.lower() in led.name.lower()]
            if color_filtered:
                leds = color_filtered
            
            # Use Thompson Sampling for LED selection
            led_scores = []
            for led in leds:
                score = self._calculate_thompson_score(led, 'led_circuit', max_current)
                led_scores.append((led, score))
            
            best_led, best_score = max(led_scores, key=lambda x: x[1])
            
            return {
                'component': {
                    'id': best_led.id,
                    'name': best_led.name,
                    'color': color,
                    'forward_voltage': best_led.voltage_rating,
                    'max_current': best_led.current_rating,
                    'package': best_led.package,
                    'cost': best_led.cost
                },
                'performance': {
                    'efficiency_score': best_score,
                    'current_rating_ok': best_led.current_rating >= max_current
                },
                'selection_method': 'thompson_sampling'
            }
            
        except Exception as e:
            logger.error(f"LED selection failed: {e}")
            return self._create_fallback_led(color)
    
    def _calculate_thompson_score(self, component: Component, circuit_type: str, 
                                target_value: float) -> float:
        """Calculate Thompson Sampling score for a component."""
        try:
            # Get historical performance data
            performance_records = self.session.query(ComponentPerformance).filter(
                ComponentPerformance.component_id == component.id,
                ComponentPerformance.circuit_type == circuit_type
            ).all()
            
            if not performance_records:
                # No historical data - use prior based on component specs
                return self._calculate_prior_score(component, target_value)
            
            # Calculate Beta distribution parameters from historical data
            successes = sum(1 for p in performance_records if p.performance_score > 0.7)
            failures = len(performance_records) - successes
            
            # Add prior (optimistic)
            alpha = successes + 1
            beta = failures + 1
            
            # Sample from Beta distribution
            sampled_score = np.random.beta(alpha, beta)
            
            # Adjust based on component specifications
            spec_score = self._calculate_spec_score(component, target_value)
            
            # Combine sampled score with specification score
            final_score = 0.7 * sampled_score + 0.3 * spec_score
            
            return final_score
            
        except Exception as e:
            logger.error(f"Thompson score calculation failed: {e}")
            return self._calculate_prior_score(component, target_value)
    
    def _calculate_prior_score(self, component: Component, target_value: float) -> float:
        """Calculate prior score based on component specifications."""
        try:
            if component.category == 'resistor':
                resistance = float(component.value)
                # Score based on how close to target resistance
                ratio = min(resistance, target_value) / max(resistance, target_value)
                spec_score = ratio
                
                # Bonus for standard values
                standard_values = [220, 330, 470, 680, 1000, 1500, 2200, 3300, 4700]
                if resistance in standard_values:
                    spec_score += 0.1
                
                # Cost factor
                cost_score = 1.0 / (1.0 + component.cost) if component.cost else 0.8
                
                return 0.6 * spec_score + 0.2 * cost_score + 0.2 * random.random()
                
            elif component.category == 'led':
                # Score based on current rating vs target
                current_score = 1.0 if component.current_rating >= target_value else 0.5
                
                # Cost factor
                cost_score = 1.0 / (1.0 + component.cost) if component.cost else 0.8
                
                return 0.5 * current_score + 0.3 * cost_score + 0.2 * random.random()
            
            return 0.5 + 0.5 * random.random()  # Default random score
            
        except Exception as e:
            logger.error(f"Prior score calculation failed: {e}")
            return 0.5
    
    def _calculate_spec_score(self, component: Component, target_value: float) -> float:
        """Calculate score based on component specifications."""
        return self._calculate_prior_score(component, target_value)
    
    def _create_fallback_resistor(self, ideal_resistance: float) -> Dict[str, Any]:
        """Create fallback resistor selection when database is empty."""
        # Find closest standard value
        standard_values = [220, 330, 470, 680, 1000, 1500, 2200, 3300, 4700, 6800, 10000]
        closest_value = min(standard_values, key=lambda x: abs(x - ideal_resistance))
        
        return {
            'component': {
                'id': None,
                'name': f'{closest_value}Ω Resistor',
                'value': str(closest_value),
                'unit': 'ohm',
                'power_rating': 0.25,
                'cost': 0.05
            },
            'performance': {
                'ideal_resistance': ideal_resistance,
                'actual_resistance': closest_value,
                'efficiency_score': 0.8
            },
            'selection_method': 'fallback_heuristic'
        }
    
    def _create_fallback_led(self, color: str) -> Dict[str, Any]:
        """Create fallback LED selection when database is empty."""
        voltage_map = {
            'red': 2.0,
            'green': 2.1,
            'blue': 3.2,
            'yellow': 2.0,
            'white': 3.2
        }
        
        forward_voltage = voltage_map.get(color.lower(), 2.0)
        
        return {
            'component': {
                'id': None,
                'name': f'{color.title()} LED 5mm',
                'color': color,
                'forward_voltage': forward_voltage,
                'max_current': 0.02,
                'package': '5mm',
                'cost': 0.10
            },
            'performance': {
                'efficiency_score': 0.8,
                'current_rating_ok': True
            },
            'selection_method': 'fallback_heuristic'
        }
    
    def update_component_performance(self, component_id: int, circuit_type: str, 
                                   performance_score: float, simulation_results: Dict[str, Any]):
        """Update component performance based on simulation results."""
        try:
            performance = ComponentPerformance(
                component_id=component_id,
                circuit_type=circuit_type,
                performance_score=performance_score,
                simulation_results=json.dumps(simulation_results)
            )
            
            self.session.add(performance)
            self.session.commit()
            
            logger.info(f"Updated performance for component {component_id}: {performance_score}")
            
        except Exception as e:
            logger.error(f"Failed to update component performance: {e}")
            self.session.rollback()
    
    def get_component_alternatives(self, component_id: int, circuit_type: str) -> List[Dict[str, Any]]:
        """Get alternative components for the given component."""
        try:
            # Get the original component
            original = self.session.query(Component).filter(Component.id == component_id).first()
            if not original:
                return []
            
            # Find similar components
            alternatives = self.session.query(Component).filter(
                Component.category == original.category,
                Component.id != component_id
            ).limit(3).all()
            
            result = []
            for alt in alternatives:
                score = self._calculate_thompson_score(alt, circuit_type, 0)
                result.append({
                    'component': {
                        'id': alt.id,
                        'name': alt.name,
                        'value': alt.value,
                        'cost': alt.cost
                    },
                    'score': score
                })
            
            return sorted(result, key=lambda x: x['score'], reverse=True)
            
        except Exception as e:
            logger.error(f"Failed to get alternatives: {e}")
            return []

# Global selector instance
component_selector = ThompsonSamplingSelector()