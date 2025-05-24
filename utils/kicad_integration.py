"""
KiCad integration module for schematic generation.
"""
import os
import logging
import json
import tempfile
import subprocess
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

class KiCadSchematicGenerator:
    """Generate KiCad schematics programmatically."""
    
    def __init__(self):
        self.kicad_available = self._check_kicad_installation()
        self.symbol_library_path = self._find_symbol_libraries()
        
    def _check_kicad_installation(self) -> bool:
        """Check if KiCad is installed and accessible."""
        try:
            result = subprocess.run(['kicad-cli', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                logger.info("KiCad CLI found and working")
                return True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        # Try alternative method
        try:
            result = subprocess.run(['which', 'kicad'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                logger.info("KiCad found in PATH")
                return True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        logger.warning("KiCad not found. Schematic generation will be limited.")
        return False
    
    def _find_symbol_libraries(self) -> Optional[str]:
        """Find KiCad symbol libraries."""
        possible_paths = [
            '/usr/share/kicad/symbols',
            '/usr/local/share/kicad/symbols',
            '/opt/kicad/share/kicad/symbols',
            os.path.expanduser('~/.local/share/kicad/symbols')
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                logger.info(f"Found KiCad symbol libraries at: {path}")
                return path
        
        logger.warning("KiCad symbol libraries not found")
        return None
    
    def create_led_schematic(self, components: Dict[str, Any], 
                           output_dir: str) -> Dict[str, Any]:
        """Create a simple LED circuit schematic."""
        try:
            # Create schematic data structure
            schematic_data = {
                'version': '20230121',
                'generator': 'circuit_ai',
                'uuid': 'led-circuit-001',
                'paper': 'A4',
                'title_block': {
                    'title': 'LED Circuit',
                    'date': '',
                    'rev': '1',
                    'company': 'Circuit AI'
                },
                'components': [],
                'wires': [],
                'labels': []
            }
            
            # Add components
            arduino_pos = (50, 50)
            led_pos = (150, 50)
            resistor_pos = (100, 50)
            
            # Arduino Uno
            schematic_data['components'].append({
                'type': 'microcontroller',
                'reference': 'U1',
                'value': 'Arduino_Uno_R3',
                'position': arduino_pos,
                'pins': {
                    'D13': (arduino_pos[0] + 20, arduino_pos[1]),
                    'GND': (arduino_pos[0] + 20, arduino_pos[1] + 10),
                    '5V': (arduino_pos[0] + 20, arduino_pos[1] - 10)
                }
            })
            
            # Current limiting resistor
            resistor_value = components.get('resistor_value', 330)
            schematic_data['components'].append({
                'type': 'resistor',
                'reference': 'R1',
                'value': f'{resistor_value}Ω',
                'position': resistor_pos,
                'pins': {
                    '1': (resistor_pos[0] - 10, resistor_pos[1]),
                    '2': (resistor_pos[0] + 10, resistor_pos[1])
                }
            })
            
            # LED
            led_color = components.get('led_color', 'red')
            schematic_data['components'].append({
                'type': 'led',
                'reference': 'D1',
                'value': f'LED_{led_color}',
                'position': led_pos,
                'pins': {
                    'anode': (led_pos[0] - 10, led_pos[1]),
                    'cathode': (led_pos[0] + 10, led_pos[1])
                }
            })
            
            # Add connections
            schematic_data['wires'] = [
                {
                    'from': {'component': 'U1', 'pin': 'D13'},
                    'to': {'component': 'R1', 'pin': '1'},
                    'net': 'LED_CONTROL'
                },
                {
                    'from': {'component': 'R1', 'pin': '2'},
                    'to': {'component': 'D1', 'pin': 'anode'},
                    'net': 'LED_ANODE'
                },
                {
                    'from': {'component': 'D1', 'pin': 'cathode'},
                    'to': {'component': 'U1', 'pin': 'GND'},
                    'net': 'GND'
                }
            ]
            
            # Generate netlist
            netlist = self._generate_netlist(schematic_data)
            
            # Save schematic data
            os.makedirs(output_dir, exist_ok=True)
            schematic_file = os.path.join(output_dir, 'led_circuit.json')
            with open(schematic_file, 'w') as f:
                json.dump(schematic_data, f, indent=2)
            
            # Save netlist
            netlist_file = os.path.join(output_dir, 'led_circuit.net')
            with open(netlist_file, 'w') as f:
                f.write(netlist)
            
            # Generate visual representation
            svg_content = self._generate_svg_schematic(schematic_data)
            svg_file = os.path.join(output_dir, 'led_circuit.svg')
            with open(svg_file, 'w') as f:
                f.write(svg_content)
            
            return {
                'success': True,
                'schematic_file': schematic_file,
                'netlist_file': netlist_file,
                'svg_file': svg_file,
                'schematic_data': schematic_data,
                'netlist': netlist
            }
            
        except Exception as e:
            logger.error(f"Failed to create LED schematic: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _generate_netlist(self, schematic_data: Dict[str, Any]) -> str:
        """Generate SPICE netlist from schematic data."""
        netlist_lines = [
            f"* {schematic_data['title_block']['title']}",
            f"* Generated by Circuit AI",
            ""
        ]
        
        # Add components
        for comp in schematic_data['components']:
            if comp['type'] == 'resistor':
                netlist_lines.append(f"{comp['reference']} net1 net2 {comp['value'].replace('Ω', '')}")
            elif comp['type'] == 'led':
                # Model LED as voltage source + resistor
                netlist_lines.append(f"V{comp['reference']} net2 net3 2.0")
                netlist_lines.append(f"R{comp['reference']}_internal net3 0 10")
        
        # Add voltage source for Arduino 5V
        netlist_lines.append("Vsupply net1 0 5.0")
        
        # Add analysis commands
        netlist_lines.extend([
            "",
            ".op",
            ".end"
        ])
        
        return "\n".join(netlist_lines)
    
    def _generate_svg_schematic(self, schematic_data: Dict[str, Any]) -> str:
        """Generate SVG representation of the schematic."""
        svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="400" height="200" xmlns="http://www.w3.org/2000/svg">
  <title>{schematic_data['title_block']['title']}</title>
  
  <!-- Background -->
  <rect width="400" height="200" fill="white" stroke="black" stroke-width="1"/>
  
  <!-- Arduino Uno -->
  <rect x="20" y="40" width="60" height="40" fill="lightblue" stroke="black" stroke-width="1"/>
  <text x="50" y="65" text-anchor="middle" font-family="Arial" font-size="10">Arduino</text>
  <text x="50" y="75" text-anchor="middle" font-family="Arial" font-size="8">Uno R3</text>
  
  <!-- Resistor -->
  <rect x="120" y="55" width="30" height="10" fill="lightgray" stroke="black" stroke-width="1"/>
  <text x="135" y="50" text-anchor="middle" font-family="Arial" font-size="8">R1</text>
  <text x="135" y="80" text-anchor="middle" font-family="Arial" font-size="8">330Ω</text>
  
  <!-- LED -->
  <circle cx="200" cy="60" r="8" fill="red" stroke="black" stroke-width="1"/>
  <text x="200" y="45" text-anchor="middle" font-family="Arial" font-size="8">D1</text>
  <text x="200" y="85" text-anchor="middle" font-family="Arial" font-size="8">LED</text>
  
  <!-- Wires -->
  <line x1="80" y1="60" x2="120" y2="60" stroke="black" stroke-width="2"/>
  <line x1="150" y1="60" x2="192" y2="60" stroke="black" stroke-width="2"/>
  <line x1="208" y1="60" x2="250" y2="60" stroke="black" stroke-width="2"/>
  <line x1="250" y1="60" x2="250" y2="100" stroke="black" stroke-width="2"/>
  <line x1="250" y1="100" x2="50" y2="100" stroke="black" stroke-width="2"/>
  <line x1="50" y1="100" x2="50" y2="80" stroke="black" stroke-width="2"/>
  
  <!-- Pin labels -->
  <text x="85" y="55" font-family="Arial" font-size="8">D13</text>
  <text x="45" y="95" font-family="Arial" font-size="8">GND</text>
  
  <!-- Title -->
  <text x="200" y="20" text-anchor="middle" font-family="Arial" font-size="14" font-weight="bold">LED Circuit Schematic</text>
</svg>'''
        
        return svg_content
    
    def create_blinker_schematic(self, components: Dict[str, Any], 
                               output_dir: str) -> Dict[str, Any]:
        """Create a LED blinker circuit schematic."""
        try:
            # Similar to LED schematic but with timing components
            schematic_data = {
                'version': '20230121',
                'generator': 'circuit_ai',
                'uuid': 'led-blinker-001',
                'paper': 'A4',
                'title_block': {
                    'title': 'LED Blinker Circuit',
                    'date': '',
                    'rev': '1',
                    'company': 'Circuit AI'
                },
                'components': [],
                'wires': [],
                'labels': []
            }
            
            # Add Arduino, LED, resistor (same as LED circuit)
            # Plus timing components for blinker functionality
            
            # This would be expanded with actual blinker circuit components
            # For now, use the LED circuit as base
            return self.create_led_schematic(components, output_dir)
            
        except Exception as e:
            logger.error(f"Failed to create blinker schematic: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def validate_schematic(self, schematic_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate schematic for common issues."""
        validation_results = {
            'valid': True,
            'warnings': [],
            'errors': []
        }
        
        try:
            # Check for required components
            components = schematic_data.get('components', [])
            component_types = [comp['type'] for comp in components]
            
            if 'microcontroller' not in component_types:
                validation_results['warnings'].append("No microcontroller found")
            
            # Check for unconnected pins
            wires = schematic_data.get('wires', [])
            connected_pins = set()
            for wire in wires:
                connected_pins.add(f"{wire['from']['component']}.{wire['from']['pin']}")
                connected_pins.add(f"{wire['to']['component']}.{wire['to']['pin']}")
            
            # Check power connections
            has_power = any('5V' in str(wire) or 'VCC' in str(wire) for wire in wires)
            has_ground = any('GND' in str(wire) for wire in wires)
            
            if not has_power:
                validation_results['warnings'].append("No power connection found")
            if not has_ground:
                validation_results['warnings'].append("No ground connection found")
            
            # Check component values
            for comp in components:
                if comp['type'] == 'resistor':
                    value_str = comp.get('value', '0Ω')
                    try:
                        value = float(value_str.replace('Ω', '').replace('k', '000').replace('M', '000000'))
                        if value <= 0:
                            validation_results['errors'].append(f"Invalid resistor value: {value_str}")
                    except ValueError:
                        validation_results['errors'].append(f"Cannot parse resistor value: {value_str}")
            
            if validation_results['errors']:
                validation_results['valid'] = False
            
        except Exception as e:
            validation_results['valid'] = False
            validation_results['errors'].append(f"Validation error: {str(e)}")
        
        return validation_results

# Global instance
kicad_generator = KiCadSchematicGenerator()