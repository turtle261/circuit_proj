"""
PCB Layout Generation Module for Phase 2.2
Implements automated component placement, routing, and manufacturing file generation.
"""

import os
import json
import logging
import tempfile
import subprocess
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, NamedTuple
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
import math

logger = logging.getLogger(__name__)

class LayerType(Enum):
    """PCB layer types."""
    TOP_COPPER = "F.Cu"
    BOTTOM_COPPER = "B.Cu"
    TOP_SILKSCREEN = "F.SilkS"
    BOTTOM_SILKSCREEN = "B.SilkS"
    TOP_SOLDERMASK = "F.Mask"
    BOTTOM_SOLDERMASK = "B.Mask"
    EDGE_CUTS = "Edge.Cuts"
    DRILL = "Drill"

class ComponentType(Enum):
    """Component types for placement optimization."""
    MICROCONTROLLER = "microcontroller"
    RESISTOR = "resistor"
    CAPACITOR = "capacitor"
    LED = "led"
    CONNECTOR = "connector"
    IC = "ic"
    CRYSTAL = "crystal"
    INDUCTOR = "inductor"

@dataclass
class ComponentPlacement:
    """Component placement information."""
    reference: str
    x: float
    y: float
    rotation: float
    layer: str
    component_type: ComponentType
    thermal_power: float = 0.0
    critical_timing: bool = False

@dataclass
class PCBConstraints:
    """PCB design constraints."""
    board_width: float = 100.0  # mm
    board_height: float = 80.0  # mm
    min_trace_width: float = 0.2  # mm
    min_via_size: float = 0.3  # mm
    min_spacing: float = 0.2  # mm
    layer_count: int = 2
    max_current_density: float = 35.0  # A/mm²

@dataclass
class RoutingNet:
    """Routing network information."""
    name: str
    pins: List[Tuple[str, str]]  # (component_ref, pin_number)
    priority: int = 1
    differential_pair: bool = False
    impedance_target: Optional[float] = None
    max_length: Optional[float] = None

@dataclass
class PCBDesign:
    """Complete PCB design data."""
    components: List[ComponentPlacement] = field(default_factory=list)
    nets: List[RoutingNet] = field(default_factory=list)
    constraints: PCBConstraints = field(default_factory=PCBConstraints)
    board_outline: List[Tuple[float, float]] = field(default_factory=list)

class ComponentPlacer:
    """Automated component placement engine."""
    
    def __init__(self, constraints: PCBConstraints):
        self.constraints = constraints
        self.placement_grid = 2.54  # mm (100 mil grid)
        
    def thermal_aware_placement(self, components: List[ComponentPlacement]) -> List[ComponentPlacement]:
        """Optimize component placement considering thermal constraints."""
        logger.info("Starting thermal-aware component placement")
        
        # Separate components by thermal characteristics
        high_power = [c for c in components if c.thermal_power > 0.5]  # >500mW
        low_power = [c for c in components if c.thermal_power <= 0.5]
        
        placed_components = []
        
        # Place high-power components first, with thermal spacing
        for i, component in enumerate(high_power):
            if i == 0:
                # Place first high-power component at center
                component.x = self.constraints.board_width / 2
                component.y = self.constraints.board_height / 2
            else:
                # Place subsequent components with thermal spacing
                min_distance = 10.0 + component.thermal_power * 5.0  # mm
                component.x, component.y = self._find_thermal_position(
                    placed_components, min_distance
                )
            
            placed_components.append(component)
            logger.info(f"Placed {component.reference} at ({component.x:.1f}, {component.y:.1f})")
        
        # Place low-power components in remaining space
        for component in low_power:
            component.x, component.y = self._find_available_position(
                placed_components, component
            )
            placed_components.append(component)
        
        logger.info(f"Completed thermal-aware placement for {len(placed_components)} components")
        return placed_components
    
    def signal_integrity_placement(self, components: List[ComponentPlacement], 
                                 critical_nets: List[RoutingNet]) -> List[ComponentPlacement]:
        """Optimize placement for signal integrity."""
        logger.info("Optimizing placement for signal integrity")
        
        # Identify critical timing components
        critical_components = []
        for net in critical_nets:
            for comp_ref, pin in net.pins:
                comp = next((c for c in components if c.reference == comp_ref), None)
                if comp:
                    comp.critical_timing = True
                    if comp not in critical_components:
                        critical_components.append(comp)
        
        # Place critical components close together
        if critical_components:
            center_x = self.constraints.board_width / 2
            center_y = self.constraints.board_height / 2
            
            for i, comp in enumerate(critical_components):
                angle = 2 * math.pi * i / len(critical_components)
                radius = 15.0  # mm
                comp.x = center_x + radius * math.cos(angle)
                comp.y = center_y + radius * math.sin(angle)
                logger.info(f"Placed critical component {comp.reference} at ({comp.x:.1f}, {comp.y:.1f})")
        
        return components
    
    def _find_thermal_position(self, existing_components: List[ComponentPlacement], 
                             min_distance: float) -> Tuple[float, float]:
        """Find position with adequate thermal spacing."""
        for attempt in range(100):  # Max attempts
            x = np.random.uniform(10, self.constraints.board_width - 10)
            y = np.random.uniform(10, self.constraints.board_height - 10)
            
            # Check distance from existing components
            valid = True
            for comp in existing_components:
                distance = math.sqrt((x - comp.x)**2 + (y - comp.y)**2)
                if distance < min_distance:
                    valid = False
                    break
            
            if valid:
                return x, y
        
        # Fallback to grid placement
        return 20.0, 20.0
    
    def _find_available_position(self, existing_components: List[ComponentPlacement],
                               component: ComponentPlacement) -> Tuple[float, float]:
        """Find available position for component."""
        grid_size = self.placement_grid
        
        for y in np.arange(10, self.constraints.board_height - 10, grid_size):
            for x in np.arange(10, self.constraints.board_width - 10, grid_size):
                # Check if position is available
                available = True
                for comp in existing_components:
                    distance = math.sqrt((x - comp.x)**2 + (y - comp.y)**2)
                    if distance < 5.0:  # Minimum spacing
                        available = False
                        break
                
                if available:
                    return x, y
        
        # Fallback position
        return 10.0, 10.0

class AdvancedRouter:
    """Multi-layer routing engine with advanced capabilities."""
    
    def __init__(self, constraints: PCBConstraints):
        self.constraints = constraints
        self.routing_grid = 0.5  # mm
        
    def differential_pair_routing(self, pairs: List[RoutingNet], 
                                impedance_target: float = 100.0) -> Dict[str, Any]:
        """Route differential pairs with impedance control."""
        logger.info(f"Routing {len(pairs)} differential pairs with {impedance_target}Ω impedance")
        
        routing_results = {}
        
        for pair in pairs:
            if not pair.differential_pair:
                continue
                
            # Calculate trace geometry for target impedance
            trace_width, trace_spacing = self._calculate_diff_pair_geometry(impedance_target)
            
            # Route the pair
            route_data = {
                'net_name': pair.name,
                'trace_width': trace_width,
                'trace_spacing': trace_spacing,
                'impedance': impedance_target,
                'length_matching': True,
                'via_count': 0
            }
            
            # Simulate routing (in real implementation, this would use actual routing algorithms)
            route_data['total_length'] = self._estimate_route_length(pair)
            route_data['layer_changes'] = 1 if self.constraints.layer_count > 2 else 0
            
            routing_results[pair.name] = route_data
            logger.info(f"Routed differential pair {pair.name}: {trace_width:.2f}mm width, {trace_spacing:.2f}mm spacing")
        
        return routing_results
    
    def power_distribution_network(self, power_nets: List[RoutingNet], 
                                 current_requirements: Dict[str, float]) -> Dict[str, Any]:
        """Design power distribution network."""
        logger.info("Designing power distribution network")
        
        pdn_results = {}
        
        for net in power_nets:
            if not net.name.startswith(('VCC', 'VDD', 'GND', '+', '-')):
                continue
                
            current_req = current_requirements.get(net.name, 0.1)  # Default 100mA
            
            # Calculate required trace width for current
            trace_width = self._calculate_power_trace_width(current_req)
            
            # Design power plane if multi-layer
            if self.constraints.layer_count >= 4:
                plane_design = {
                    'use_plane': True,
                    'plane_layer': 'Power' if 'VCC' in net.name or 'VDD' in net.name else 'Ground',
                    'via_stitching': True,
                    'decoupling_caps': self._place_decoupling_caps(net)
                }
            else:
                plane_design = {
                    'use_plane': False,
                    'trace_width': trace_width,
                    'pour_zones': True
                }
            
            pdn_results[net.name] = {
                'current_capacity': current_req,
                'trace_width': trace_width,
                'voltage_drop': self._estimate_voltage_drop(net, current_req, trace_width),
                'design': plane_design
            }
            
            logger.info(f"PDN for {net.name}: {current_req:.3f}A, {trace_width:.2f}mm width")
        
        return pdn_results
    
    def _calculate_diff_pair_geometry(self, impedance: float) -> Tuple[float, float]:
        """Calculate differential pair trace geometry."""
        # Simplified calculation for 2-layer board
        # Real implementation would use field solvers
        if impedance == 100.0:
            return 0.2, 0.2  # width, spacing in mm
        elif impedance == 90.0:
            return 0.25, 0.15
        else:
            # Linear interpolation
            width = 0.2 + (100 - impedance) * 0.001
            spacing = 0.2 - (100 - impedance) * 0.001
            return max(width, 0.1), max(spacing, 0.1)
    
    def _calculate_power_trace_width(self, current: float) -> float:
        """Calculate trace width for given current."""
        # IPC-2221 formula approximation
        # W = (I / (k * ΔT^b))^(1/c) where k, b, c are constants
        temp_rise = 10.0  # °C
        k = 0.048  # for external traces
        b = 0.44
        c = 0.725
        
        width_mils = (current / (k * (temp_rise ** b))) ** (1/c)
        width_mm = width_mils * 0.0254  # Convert mils to mm
        
        return max(width_mm, self.constraints.min_trace_width)
    
    def _estimate_route_length(self, net: RoutingNet) -> float:
        """Estimate routing length for a net."""
        # Simplified estimation - real implementation would use actual placement
        return 20.0 + len(net.pins) * 5.0  # mm
    
    def _estimate_voltage_drop(self, net: RoutingNet, current: float, trace_width: float) -> float:
        """Estimate voltage drop in power net."""
        # Simplified calculation
        length = self._estimate_route_length(net)
        resistance = 0.017 * length / (trace_width * 0.035)  # Ohms (35µm copper)
        return current * resistance  # Volts
    
    def _place_decoupling_caps(self, net: RoutingNet) -> List[Dict[str, Any]]:
        """Determine decoupling capacitor placement."""
        caps = []
        
        # Basic decoupling strategy
        for i, (comp_ref, pin) in enumerate(net.pins):
            if 'IC' in comp_ref or 'U' in comp_ref:
                caps.append({
                    'value': '100nF',
                    'package': '0603',
                    'placement': f'near_{comp_ref}',
                    'distance': 2.0  # mm
                })
        
        return caps

class AdvancedDRC:
    """Design Rule Checking engine."""
    
    def __init__(self, constraints: PCBConstraints):
        self.constraints = constraints
        
    def comprehensive_rule_check(self, pcb_design: PCBDesign) -> Dict[str, Any]:
        """Perform comprehensive design rule checking."""
        logger.info("Starting comprehensive design rule check")
        
        violations = []
        warnings = []
        
        # Electrical connectivity verification
        electrical_check = self._check_electrical_connectivity(pcb_design)
        violations.extend(electrical_check.get('violations', []))
        warnings.extend(electrical_check.get('warnings', []))
        
        # Manufacturing constraint validation
        manufacturing_check = self._check_manufacturing_constraints(pcb_design)
        violations.extend(manufacturing_check.get('violations', []))
        warnings.extend(manufacturing_check.get('warnings', []))
        
        # Signal integrity rule checking
        si_check = self._check_signal_integrity_rules(pcb_design)
        violations.extend(si_check.get('violations', []))
        warnings.extend(si_check.get('warnings', []))
        
        # Thermal management verification
        thermal_check = self._check_thermal_management(pcb_design)
        violations.extend(thermal_check.get('violations', []))
        warnings.extend(thermal_check.get('warnings', []))
        
        results = {
            'violations': violations,
            'warnings': warnings,
            'violation_count': len(violations),
            'warning_count': len(warnings),
            'pass': len(violations) == 0
        }
        
        logger.info(f"DRC completed: {len(violations)} violations, {len(warnings)} warnings")
        return results
    
    def _check_electrical_connectivity(self, pcb_design: PCBDesign) -> Dict[str, List[str]]:
        """Check electrical connectivity."""
        violations = []
        warnings = []
        
        # Check for unconnected nets
        for net in pcb_design.nets:
            if len(net.pins) < 2:
                violations.append(f"Net {net.name} has insufficient connections")
        
        # Check for short circuits (simplified)
        component_positions = {comp.reference: (comp.x, comp.y) for comp in pcb_design.components}
        
        for i, comp1 in enumerate(pcb_design.components):
            for comp2 in pcb_design.components[i+1:]:
                distance = math.sqrt((comp1.x - comp2.x)**2 + (comp1.y - comp2.y)**2)
                if distance < 2.0:  # Too close
                    warnings.append(f"Components {comp1.reference} and {comp2.reference} may be too close")
        
        return {'violations': violations, 'warnings': warnings}
    
    def _check_manufacturing_constraints(self, pcb_design: PCBDesign) -> Dict[str, List[str]]:
        """Check manufacturing constraints."""
        violations = []
        warnings = []
        
        # Check minimum trace width
        min_width = self.constraints.min_trace_width
        if min_width < 0.1:
            violations.append(f"Minimum trace width {min_width}mm is below manufacturing limit")
        
        # Check via sizes
        min_via = self.constraints.min_via_size
        if min_via < 0.2:
            violations.append(f"Minimum via size {min_via}mm is below manufacturing limit")
        
        # Check board dimensions
        if pcb_design.constraints.board_width > 200 or pcb_design.constraints.board_height > 200:
            warnings.append("Large board size may increase manufacturing cost")
        
        return {'violations': violations, 'warnings': warnings}
    
    def _check_signal_integrity_rules(self, pcb_design: PCBDesign) -> Dict[str, List[str]]:
        """Check signal integrity rules."""
        violations = []
        warnings = []
        
        # Check for high-speed signals
        for net in pcb_design.nets:
            if net.impedance_target and net.impedance_target > 0:
                if not net.differential_pair and net.impedance_target < 50:
                    warnings.append(f"Net {net.name} has unusual single-ended impedance")
                elif net.differential_pair and (net.impedance_target < 90 or net.impedance_target > 110):
                    warnings.append(f"Differential pair {net.name} has unusual impedance target")
        
        # Check critical timing paths
        critical_components = [c for c in pcb_design.components if c.critical_timing]
        if len(critical_components) > 1:
            max_distance = 0
            for i, comp1 in enumerate(critical_components):
                for comp2 in critical_components[i+1:]:
                    distance = math.sqrt((comp1.x - comp2.x)**2 + (comp1.y - comp2.y)**2)
                    max_distance = max(max_distance, distance)
            
            if max_distance > 30:  # mm
                warnings.append("Critical timing components are far apart - consider closer placement")
        
        return {'violations': violations, 'warnings': warnings}
    
    def _check_thermal_management(self, pcb_design: PCBDesign) -> Dict[str, List[str]]:
        """Check thermal management."""
        violations = []
        warnings = []
        
        # Check high-power component spacing
        high_power_components = [c for c in pcb_design.components if c.thermal_power > 0.5]
        
        for i, comp1 in enumerate(high_power_components):
            for comp2 in high_power_components[i+1:]:
                distance = math.sqrt((comp1.x - comp2.x)**2 + (comp1.y - comp2.y)**2)
                min_distance = 5.0 + (comp1.thermal_power + comp2.thermal_power) * 2.0
                
                if distance < min_distance:
                    warnings.append(f"High-power components {comp1.reference} and {comp2.reference} may need more thermal spacing")
        
        # Check for thermal vias near high-power components
        total_power = sum(c.thermal_power for c in pcb_design.components)
        if total_power > 2.0 and pcb_design.constraints.layer_count >= 4:
            warnings.append("Consider adding thermal vias for high-power design")
        
        return {'violations': violations, 'warnings': warnings}

class ManufacturingOutputs:
    """Generate manufacturing files and documentation."""
    
    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
    def generate_gerber_files(self, pcb_design: PCBDesign, project_name: str) -> Dict[str, str]:
        """Generate Gerber files for manufacturing."""
        logger.info(f"Generating Gerber files for {project_name}")
        
        gerber_files = {}
        
        # Generate each layer
        layers = [
            (LayerType.TOP_COPPER, f"{project_name}-F_Cu.gbr"),
            (LayerType.BOTTOM_COPPER, f"{project_name}-B_Cu.gbr"),
            (LayerType.TOP_SILKSCREEN, f"{project_name}-F_SilkS.gbr"),
            (LayerType.BOTTOM_SILKSCREEN, f"{project_name}-B_SilkS.gbr"),
            (LayerType.TOP_SOLDERMASK, f"{project_name}-F_Mask.gbr"),
            (LayerType.BOTTOM_SOLDERMASK, f"{project_name}-B_Mask.gbr"),
            (LayerType.EDGE_CUTS, f"{project_name}-Edge_Cuts.gbr")
        ]
        
        for layer_type, filename in layers:
            file_path = self.output_dir / filename
            gerber_content = self._generate_gerber_layer(pcb_design, layer_type)
            
            with open(file_path, 'w') as f:
                f.write(gerber_content)
            
            gerber_files[layer_type.value] = str(file_path)
            logger.info(f"Generated {filename}")
        
        # Generate drill file
        drill_file = f"{project_name}.drl"
        drill_path = self.output_dir / drill_file
        drill_content = self._generate_drill_file(pcb_design)
        
        with open(drill_path, 'w') as f:
            f.write(drill_content)
        
        gerber_files['drill'] = str(drill_path)
        
        # Generate pick and place file
        pnp_file = f"{project_name}-top-pos.csv"
        pnp_path = self.output_dir / pnp_file
        pnp_content = self._generate_pick_place_file(pcb_design)
        
        with open(pnp_path, 'w') as f:
            f.write(pnp_content)
        
        gerber_files['pick_place'] = str(pnp_path)
        
        logger.info(f"Generated {len(gerber_files)} manufacturing files")
        return gerber_files
    
    def generate_assembly_drawings(self, pcb_design: PCBDesign, project_name: str) -> Dict[str, str]:
        """Generate assembly documentation."""
        logger.info(f"Generating assembly documentation for {project_name}")
        
        assembly_files = {}
        
        # Assembly drawing (simplified text format)
        assembly_drawing = self._generate_assembly_drawing(pcb_design)
        assembly_path = self.output_dir / f"{project_name}-assembly.txt"
        
        with open(assembly_path, 'w') as f:
            f.write(assembly_drawing)
        
        assembly_files['assembly_drawing'] = str(assembly_path)
        
        # Assembly notes
        assembly_notes = self._generate_assembly_notes(pcb_design)
        notes_path = self.output_dir / f"{project_name}-assembly-notes.txt"
        
        with open(notes_path, 'w') as f:
            f.write(assembly_notes)
        
        assembly_files['assembly_notes'] = str(notes_path)
        
        # Test points documentation
        test_points = self._generate_test_points(pcb_design)
        test_path = self.output_dir / f"{project_name}-test-points.txt"
        
        with open(test_path, 'w') as f:
            f.write(test_points)
        
        assembly_files['test_points'] = str(test_path)
        
        logger.info(f"Generated {len(assembly_files)} assembly documentation files")
        return assembly_files
    
    def _generate_gerber_layer(self, pcb_design: PCBDesign, layer_type: LayerType) -> str:
        """Generate Gerber content for a specific layer."""
        # Simplified Gerber generation
        gerber_content = [
            "G04 #@! TF.GenerationSoftware,Circuit AI,PCB Layout Generator*",
            f"G04 #@! TF.FileFunction,{layer_type.value}*",
            "G04 #@! TF.SameCoordinates,Original*",
            "%FSLAX36Y36*%",
            "%MOMM*%",
            "%TA.AperFunction,Conductor*%",
            "%ADD10C,0.200000*%",  # 0.2mm trace
            "%ADD11C,0.300000*%",  # 0.3mm via
            "G04 Layer content*",
        ]
        
        if layer_type == LayerType.TOP_COPPER:
            # Add component pads and traces
            for component in pcb_design.components:
                if component.layer == "F.Cu" or component.layer == "top":
                    x_gerber = int(component.x * 1000000)  # Convert to Gerber units
                    y_gerber = int(component.y * 1000000)
                    gerber_content.append(f"X{x_gerber}Y{y_gerber}D03*")  # Flash pad
        
        elif layer_type == LayerType.EDGE_CUTS:
            # Add board outline
            if pcb_design.board_outline:
                gerber_content.append("G01*")  # Linear interpolation
                for i, (x, y) in enumerate(pcb_design.board_outline):
                    x_gerber = int(x * 1000000)
                    y_gerber = int(y * 1000000)
                    if i == 0:
                        gerber_content.append(f"X{x_gerber}Y{y_gerber}D02*")  # Move
                    else:
                        gerber_content.append(f"X{x_gerber}Y{y_gerber}D01*")  # Draw
            else:
                # Default rectangular outline
                w = int(pcb_design.constraints.board_width * 1000000)
                h = int(pcb_design.constraints.board_height * 1000000)
                gerber_content.extend([
                    "X0Y0D02*",
                    f"X{w}Y0D01*",
                    f"X{w}Y{h}D01*",
                    f"X0Y{h}D01*",
                    "X0Y0D01*"
                ])
        
        gerber_content.append("M02*")  # End of file
        return "\n".join(gerber_content)
    
    def _generate_drill_file(self, pcb_design: PCBDesign) -> str:
        """Generate Excellon drill file."""
        drill_content = [
            "M48",
            "INCH",
            "T1C0.0118",  # 0.3mm drill
            "%",
            "G90",
            "G05",
            "T1"
        ]
        
        # Add drill holes for vias and component holes
        for component in pcb_design.components:
            x_inch = component.x / 25.4  # Convert mm to inches
            y_inch = component.y / 25.4
            drill_content.append(f"X{x_inch:.4f}Y{y_inch:.4f}")
        
        drill_content.append("M30")
        return "\n".join(drill_content)
    
    def _generate_pick_place_file(self, pcb_design: PCBDesign) -> str:
        """Generate pick and place file."""
        pnp_content = ["Ref,Val,Package,PosX,PosY,Rot,Side"]
        
        for component in pcb_design.components:
            side = "top" if component.layer in ["F.Cu", "top"] else "bottom"
            pnp_content.append(
                f"{component.reference},"
                f"{component.component_type.value},"
                f"0603,"  # Default package
                f"{component.x:.3f},"
                f"{component.y:.3f},"
                f"{component.rotation:.1f},"
                f"{side}"
            )
        
        return "\n".join(pnp_content)
    
    def _generate_assembly_drawing(self, pcb_design: PCBDesign) -> str:
        """Generate assembly drawing documentation."""
        content = [
            "PCB ASSEMBLY DRAWING",
            "=" * 50,
            "",
            f"Board Size: {pcb_design.constraints.board_width} x {pcb_design.constraints.board_height} mm",
            f"Layer Count: {pcb_design.constraints.layer_count}",
            "",
            "COMPONENT PLACEMENT:",
            "-" * 30
        ]
        
        for component in pcb_design.components:
            content.append(
                f"{component.reference:8} | "
                f"({component.x:6.1f}, {component.y:6.1f}) | "
                f"{component.rotation:5.1f}° | "
                f"{component.component_type.value}"
            )
        
        return "\n".join(content)
    
    def _generate_assembly_notes(self, pcb_design: PCBDesign) -> str:
        """Generate assembly notes."""
        content = [
            "PCB ASSEMBLY NOTES",
            "=" * 50,
            "",
            "GENERAL ASSEMBLY INSTRUCTIONS:",
            "1. Handle PCB with anti-static precautions",
            "2. Use appropriate soldering temperature profiles",
            "3. Inspect all solder joints after assembly",
            "4. Perform electrical testing before final assembly",
            "",
            "COMPONENT-SPECIFIC NOTES:",
        ]
        
        # Add specific notes for different component types
        component_types = set(c.component_type for c in pcb_design.components)
        
        for comp_type in component_types:
            if comp_type == ComponentType.MICROCONTROLLER:
                content.append("- Microcontroller: Ensure proper orientation, use flux")
            elif comp_type == ComponentType.LED:
                content.append("- LEDs: Check polarity before soldering")
            elif comp_type == ComponentType.CRYSTAL:
                content.append("- Crystal: Handle carefully, avoid mechanical stress")
        
        # Add thermal considerations
        high_power_components = [c for c in pcb_design.components if c.thermal_power > 0.5]
        if high_power_components:
            content.extend([
                "",
                "THERMAL CONSIDERATIONS:",
                "- High-power components require adequate heat sinking",
                "- Consider thermal interface materials where appropriate"
            ])
        
        return "\n".join(content)
    
    def _generate_test_points(self, pcb_design: PCBDesign) -> str:
        """Generate test points documentation."""
        content = [
            "TEST POINTS DOCUMENTATION",
            "=" * 50,
            "",
            "RECOMMENDED TEST POINTS:",
        ]
        
        # Identify critical nets for test points
        power_nets = [net for net in pcb_design.nets if any(
            keyword in net.name.upper() for keyword in ['VCC', 'VDD', 'GND', 'POWER']
        )]
        
        for net in power_nets:
            content.append(f"- {net.name}: Power supply verification")
        
        # Add general test recommendations
        content.extend([
            "",
            "QUALITY CONTROL CHECKPOINTS:",
            "1. Visual inspection of solder joints",
            "2. Continuity testing of critical nets",
            "3. Power supply voltage verification",
            "4. Functional testing of key circuits"
        ])
        
        return "\n".join(content)

class IntelligentBOM:
    """Intelligent Bill of Materials generator with supplier integration."""
    
    def __init__(self):
        self.supplier_apis = {
            'digikey': 'https://api.digikey.com',
            'mouser': 'https://api.mouser.com',
            'lcsc': 'https://lcsc.com/api'
        }
        
    def generate_optimized_bom(self, components: List[ComponentPlacement], 
                             constraints: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate optimized BOM with real-time pricing and availability."""
        logger.info(f"Generating optimized BOM for {len(components)} components")
        
        if constraints is None:
            constraints = {'max_cost': 100.0, 'preferred_suppliers': ['digikey', 'mouser']}
        
        bom_data = {
            'components': [],
            'total_cost': 0.0,
            'availability_status': 'good',
            'supplier_recommendations': [],
            'alternatives': []
        }
        
        # Group components by type and value
        component_groups = self._group_components(components)
        
        for group_id, group_components in component_groups.items():
            component_info = self._get_component_info(group_components[0])
            
            # Get pricing and availability (simulated)
            pricing_info = self._get_pricing_info(component_info)
            
            bom_entry = {
                'group_id': group_id,
                'references': [c.reference for c in group_components],
                'quantity': len(group_components),
                'component_type': group_components[0].component_type.value,
                'description': component_info['description'],
                'manufacturer': component_info['manufacturer'],
                'part_number': component_info['part_number'],
                'unit_cost': pricing_info['unit_cost'],
                'total_cost': pricing_info['unit_cost'] * len(group_components),
                'availability': pricing_info['availability'],
                'lead_time': pricing_info['lead_time'],
                'supplier': pricing_info['supplier']
            }
            
            bom_data['components'].append(bom_entry)
            bom_data['total_cost'] += bom_entry['total_cost']
        
        # Generate supplier recommendations
        bom_data['supplier_recommendations'] = self._generate_supplier_recommendations(bom_data)
        
        # Find alternative components
        bom_data['alternatives'] = self._find_alternative_components(bom_data['components'])
        
        logger.info(f"Generated BOM: {len(bom_data['components'])} line items, ${bom_data['total_cost']:.2f} total")
        return bom_data
    
    def _group_components(self, components: List[ComponentPlacement]) -> Dict[str, List[ComponentPlacement]]:
        """Group identical components together."""
        groups = {}
        
        for component in components:
            # Create group key based on component type and characteristics
            group_key = f"{component.component_type.value}"
            
            if group_key not in groups:
                groups[group_key] = []
            groups[group_key].append(component)
        
        return groups
    
    def _get_component_info(self, component: ComponentPlacement) -> Dict[str, str]:
        """Get component information."""
        # Simulated component database
        component_db = {
            ComponentType.RESISTOR: {
                'description': '0603 Resistor, 1% tolerance',
                'manufacturer': 'Yageo',
                'part_number': 'RC0603FR-07220RL'
            },
            ComponentType.CAPACITOR: {
                'description': '0603 Ceramic Capacitor, X7R',
                'manufacturer': 'Murata',
                'part_number': 'GRM188R71H104KA93D'
            },
            ComponentType.LED: {
                'description': '0603 LED, Red, 2V',
                'manufacturer': 'Kingbright',
                'part_number': 'APT1608EC'
            },
            ComponentType.MICROCONTROLLER: {
                'description': 'Arduino Uno R3',
                'manufacturer': 'Arduino',
                'part_number': 'A000066'
            }
        }
        
        return component_db.get(component.component_type, {
            'description': f'{component.component_type.value} component',
            'manufacturer': 'Generic',
            'part_number': 'TBD'
        })
    
    def _get_pricing_info(self, component_info: Dict[str, str]) -> Dict[str, Any]:
        """Get pricing and availability information."""
        # Simulated pricing data
        base_prices = {
            'RC0603FR-07220RL': 0.02,  # Resistor
            'GRM188R71H104KA93D': 0.05,  # Capacitor
            'APT1608EC': 0.15,  # LED
            'A000066': 25.00  # Arduino
        }
        
        part_number = component_info.get('part_number', 'TBD')
        base_price = base_prices.get(part_number, 1.00)
        
        return {
            'unit_cost': base_price,
            'availability': 'In Stock' if base_price < 10 else 'Limited Stock',
            'lead_time': '1-2 weeks' if base_price < 10 else '4-6 weeks',
            'supplier': 'DigiKey'
        }
    
    def _generate_supplier_recommendations(self, bom_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate supplier recommendations."""
        recommendations = []
        
        total_cost = bom_data['total_cost']
        
        if total_cost < 50:
            recommendations.append({
                'supplier': 'LCSC',
                'reason': 'Cost-effective for low-value orders',
                'estimated_savings': '15-25%'
            })
        
        if total_cost > 100:
            recommendations.append({
                'supplier': 'DigiKey',
                'reason': 'Reliable supply chain for production',
                'estimated_savings': 'Volume discounts available'
            })
        
        recommendations.append({
            'supplier': 'Mouser',
            'reason': 'Good alternative source',
            'estimated_savings': 'Price matching available'
        })
        
        return recommendations
    
    def _find_alternative_components(self, components: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Find alternative components for cost optimization."""
        alternatives = []
        
        for component in components:
            if component['unit_cost'] > 1.0:  # Only suggest alternatives for expensive parts
                alt_part = {
                    'original_part': component['part_number'],
                    'alternative_part': f"ALT-{component['part_number']}",
                    'cost_savings': component['unit_cost'] * 0.2,
                    'notes': 'Functionally equivalent, different manufacturer'
                }
                alternatives.append(alt_part)
        
        return alternatives

class PCBLayoutEngine:
    """Main PCB layout generation engine that orchestrates all components."""
    
    def __init__(self, output_dir: str = "output"):
        self.output_dir = output_dir
        self.placer = None
        self.router = None
        self.drc = None
        self.manufacturing = ManufacturingOutputs(output_dir)
        self.bom_generator = IntelligentBOM()
        
    def generate_pcb_layout(self, circuit_data: Dict[str, Any], 
                          project_name: str = "circuit") -> Dict[str, Any]:
        """Generate complete PCB layout from circuit data."""
        logger.info(f"Starting PCB layout generation for {project_name}")
        logger.info(f"PCB layout engine input - circuit_data type: {type(circuit_data)}, content: {circuit_data}")
        
        try:
            # Validate input data
            if not isinstance(circuit_data, dict):
                raise ValueError(f"Expected dict for circuit_data, got {type(circuit_data)}")
            
            # Parse circuit data and create PCB design
            pcb_design = self._parse_circuit_data(circuit_data)
            
            # Initialize engines with constraints
            self.placer = ComponentPlacer(pcb_design.constraints)
            self.router = AdvancedRouter(pcb_design.constraints)
            self.drc = AdvancedDRC(pcb_design.constraints)
            
            # Component placement optimization
            logger.info("Optimizing component placement...")
            pcb_design.components = self.placer.thermal_aware_placement(pcb_design.components)
            
            # Signal integrity optimization
            critical_nets = [net for net in pcb_design.nets if net.priority > 5]
            pcb_design.components = self.placer.signal_integrity_placement(
                pcb_design.components, critical_nets
            )
            
            # Routing
            logger.info("Performing advanced routing...")
            diff_pairs = [net for net in pcb_design.nets if net.differential_pair]
            routing_results = self.router.differential_pair_routing(diff_pairs)
            
            power_nets = [net for net in pcb_design.nets if any(
                keyword in net.name.upper() for keyword in ['VCC', 'VDD', 'GND', 'POWER']
            )]
            current_requirements = {net.name: 0.5 for net in power_nets}  # Default 500mA
            pdn_results = self.router.power_distribution_network(power_nets, current_requirements)
            
            # Design rule checking
            logger.info("Performing design rule check...")
            drc_results = self.drc.comprehensive_rule_check(pcb_design)
            
            # Generate manufacturing files
            logger.info("Generating manufacturing files...")
            gerber_files = self.manufacturing.generate_gerber_files(pcb_design, project_name)
            assembly_docs = self.manufacturing.generate_assembly_drawings(pcb_design, project_name)
            
            # Generate BOM
            logger.info("Generating optimized BOM...")
            bom_data = self.bom_generator.generate_optimized_bom(pcb_design.components)
            
            # Compile results
            layout_results = {
                'project_name': project_name,
                'pcb_design': pcb_design,
                'placement_results': {
                    'component_count': len(pcb_design.components),
                    'board_utilization': self._calculate_board_utilization(pcb_design),
                    'thermal_zones': self._identify_thermal_zones(pcb_design)
                },
                'routing_results': {
                    'differential_pairs': routing_results,
                    'power_distribution': pdn_results,
                    'total_nets': len(pcb_design.nets)
                },
                'drc_results': drc_results,
                'manufacturing_files': gerber_files,
                'assembly_documentation': assembly_docs,
                'bom': bom_data,
                'success': drc_results['pass'],
                'summary': self._generate_layout_summary(pcb_design, drc_results, bom_data)
            }
            
            logger.info(f"PCB layout generation completed successfully for {project_name}")
            return layout_results
            
        except Exception as e:
            logger.error(f"PCB layout generation failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'project_name': project_name
            }
    
    def _parse_circuit_data(self, circuit_data: Dict[str, Any]) -> PCBDesign:
        """Parse circuit data into PCB design structure."""
        logger.info(f"_parse_circuit_data called with type: {type(circuit_data)}")
        pcb_design = PCBDesign()
        
        # Set board constraints
        logger.info(f"About to call circuit_data.get('constraints') on {type(circuit_data)}")
        constraints_data = circuit_data.get('constraints', {})
        pcb_design.constraints = PCBConstraints(
            board_width=constraints_data.get('board_width', 80.0),  # mm
            board_height=constraints_data.get('board_height', 60.0),  # mm
            layer_count=constraints_data.get('layer_count', 2),
            min_trace_width=constraints_data.get('min_trace_width', 0.2),
            min_via_size=constraints_data.get('min_via_size', 0.3)
        )
        
        # Parse components
        components_data = circuit_data.get('components', [])
        logger.info(f"components_data type: {type(components_data)}, content: {components_data}")
        
        # Handle both list and dict formats for components
        if isinstance(components_data, dict):
            # Convert dict format to list format
            component_list = []
            for comp_type, comp_value in components_data.items():
                if comp_value is not None:
                    component_list.append({
                        'type': comp_type,
                        'value': comp_value,
                        'reference': f'{comp_type.upper()}1'
                    })
                else:
                    # Create default component entry
                    component_list.append({
                        'type': comp_type,
                        'value': '220R' if comp_type == 'resistor' else 'Red LED',
                        'reference': f'{comp_type.upper()}1'
                    })
            components_data = component_list
            
        for i, comp_data in enumerate(components_data):
            logger.info(f"Processing component {i}: type={type(comp_data)}, content={comp_data}")
            comp_type = self._determine_component_type(comp_data)
            thermal_power = self._estimate_thermal_power(comp_data)
            
            component = ComponentPlacement(
                reference=comp_data.get('reference', f'C{i+1}'),
                x=0.0,  # Will be set by placement algorithm
                y=0.0,
                rotation=0.0,
                layer="F.Cu",
                component_type=comp_type,
                thermal_power=thermal_power
            )
            pcb_design.components.append(component)
        
        # Parse nets
        connections = circuit_data.get('connections', [])
        net_dict = {}
        
        for conn in connections:
            net_name = conn.get('net', f'Net_{len(net_dict)}')
            if net_name not in net_dict:
                net_dict[net_name] = RoutingNet(
                    name=net_name,
                    pins=[],
                    priority=self._determine_net_priority(net_name)
                )
            
            # Add pins to net
            from_pin = (conn.get('from', ''), conn.get('from_pin', '1'))
            to_pin = (conn.get('to', ''), conn.get('to_pin', '1'))
            
            if from_pin not in net_dict[net_name].pins:
                net_dict[net_name].pins.append(from_pin)
            if to_pin not in net_dict[net_name].pins:
                net_dict[net_name].pins.append(to_pin)
        
        pcb_design.nets = list(net_dict.values())
        
        # Set default board outline
        w, h = pcb_design.constraints.board_width, pcb_design.constraints.board_height
        pcb_design.board_outline = [(0, 0), (w, 0), (w, h), (0, h), (0, 0)]
        
        return pcb_design
    
    def _determine_component_type(self, comp_data: Dict[str, Any]) -> ComponentType:
        """Determine component type from component data."""
        comp_name = comp_data.get('type', '').lower()
        reference = comp_data.get('reference', '').upper()
        
        if 'arduino' in comp_name or 'microcontroller' in comp_name or reference.startswith('U'):
            return ComponentType.MICROCONTROLLER
        elif 'resistor' in comp_name or reference.startswith('R'):
            return ComponentType.RESISTOR
        elif 'capacitor' in comp_name or reference.startswith('C'):
            return ComponentType.CAPACITOR
        elif 'led' in comp_name or reference.startswith('D'):
            return ComponentType.LED
        elif 'connector' in comp_name or reference.startswith('J'):
            return ComponentType.CONNECTOR
        elif 'crystal' in comp_name or reference.startswith('Y'):
            return ComponentType.CRYSTAL
        elif 'inductor' in comp_name or reference.startswith('L'):
            return ComponentType.INDUCTOR
        else:
            return ComponentType.IC
    
    def _estimate_thermal_power(self, comp_data: Dict[str, Any]) -> float:
        """Estimate thermal power dissipation."""
        comp_type = comp_data.get('type', '').lower()
        
        if 'arduino' in comp_type or 'microcontroller' in comp_type:
            return 0.5  # 500mW
        elif 'led' in comp_type:
            return 0.1  # 100mW
        elif 'resistor' in comp_type:
            return 0.05  # 50mW
        else:
            return 0.01  # 10mW
    
    def _determine_net_priority(self, net_name: str) -> int:
        """Determine routing priority for net."""
        net_upper = net_name.upper()
        
        if any(keyword in net_upper for keyword in ['CLK', 'CLOCK']):
            return 10  # Highest priority
        elif any(keyword in net_upper for keyword in ['VCC', 'VDD', 'GND', 'POWER']):
            return 8   # High priority
        elif any(keyword in net_upper for keyword in ['DATA', 'SDA', 'SCL']):
            return 6   # Medium-high priority
        else:
            return 3   # Normal priority
    
    def _calculate_board_utilization(self, pcb_design: PCBDesign) -> float:
        """Calculate board area utilization."""
        total_area = pcb_design.constraints.board_width * pcb_design.constraints.board_height
        
        # Estimate component area (simplified)
        component_area = len(pcb_design.components) * 4.0  # 2x2mm per component average
        
        return min(component_area / total_area * 100, 100.0)
    
    def _identify_thermal_zones(self, pcb_design: PCBDesign) -> List[Dict[str, Any]]:
        """Identify thermal zones on the board."""
        thermal_zones = []
        
        high_power_components = [c for c in pcb_design.components if c.thermal_power > 0.2]
        
        for component in high_power_components:
            zone = {
                'component': component.reference,
                'center_x': component.x,
                'center_y': component.y,
                'power': component.thermal_power,
                'radius': 5.0 + component.thermal_power * 10.0  # mm
            }
            thermal_zones.append(zone)
        
        return thermal_zones
    
    def _generate_layout_summary(self, pcb_design: PCBDesign, 
                                drc_results: Dict[str, Any], 
                                bom_data: Dict[str, Any]) -> str:
        """Generate layout summary report."""
        summary_lines = [
            f"PCB Layout Summary",
            f"==================",
            f"Board Size: {pcb_design.constraints.board_width} x {pcb_design.constraints.board_height} mm",
            f"Layer Count: {pcb_design.constraints.layer_count}",
            f"Components: {len(pcb_design.components)}",
            f"Nets: {len(pcb_design.nets)}",
            f"",
            f"Design Rule Check:",
            f"  Violations: {drc_results['violation_count']}",
            f"  Warnings: {drc_results['warning_count']}",
            f"  Status: {'PASS' if drc_results['pass'] else 'FAIL'}",
            f"",
            f"Bill of Materials:",
            f"  Line Items: {len(bom_data['components'])}",
            f"  Total Cost: ${bom_data['total_cost']:.2f}",
            f"  Availability: {bom_data['availability_status']}",
        ]
        
        return "\n".join(summary_lines)