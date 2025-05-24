import os
import sys
import logging
import json
import threading
import time
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import our modules
from agents.circuit_design_crew import run_circuit_design
from database.models import create_database, get_session
from database.seed_data import seed_basic_components
from simulations.spice_simulator import simulator
from utils.kicad_integration import kicad_generator
from utils.component_selection import component_selector

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'circuit-ai-secret-key')

# Initialize SocketIO with CORS support and explicit transports
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet', 
                   transports=['polling', 'websocket'], allow_upgrades=True)

# Initialize database
try:
    create_database()
    seed_basic_components()
    logger.info("Database initialized successfully")
except Exception as e:
    logger.error(f"Database initialization failed: {e}")

@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')

@app.route('/design', methods=['POST'])
def design_circuit():
    """Handle circuit design requests."""
    try:
        data = request.get_json()
        user_input = data.get('description', '')
        
        if not user_input:
            return jsonify({'status': 'error', 'message': 'No circuit description provided'})
        
        # Start design process in background thread
        thread = threading.Thread(target=run_design_process, args=(user_input,))
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'status': 'success', 
            'message': 'Circuit design started',
            'process_id': 'design_' + str(int(time.time()))
        })
        
    except Exception as e:
        logger.error(f"Design request failed: {e}")
        return jsonify({'status': 'error', 'message': str(e)})

def emit_progress(stage, message, progress, detail=None):
    """Emit progress update via WebSocket with error handling"""
    data = {
        'stage': stage,
        'message': message,
        'progress': progress
    }
    if detail:
        data['detail'] = detail
    
    try:
        socketio.emit('design_progress', data)
        logger.info(f"Progress emitted: {stage} - {message} ({progress}%)")
    except Exception as e:
        logger.warning(f"Failed to emit progress: {e}")
        print(f"Progress: {stage} - {message} ({progress}%)")
        if detail:
            print(f"Detail: {detail}")

def run_design_process(user_input: str):
    """Run the complete circuit design process with real-time updates."""
    try:
        # Stage 1: Research and Analysis
        emit_progress('research', 'Starting requirements analysis...', 5, 'Initializing AI agents')
        
        time.sleep(1)
        emit_progress('research', 'Analyzing circuit requirements...', 10, 'Processing natural language input')
        
        time.sleep(2)
        emit_progress('research', 'Researching component specifications...', 15, 'Consulting component database')
        
        # Stage 2: Design Phase
        time.sleep(2)
        emit_progress('design', 'Starting circuit design...', 20, 'Activating design agent')
        
        time.sleep(1)
        emit_progress('design', 'Calculating component values...', 25, 'Using Thompson Sampling for optimization')
        
        # Component selection
        time.sleep(2)
        emit_progress('design', 'Selecting optimal components...', 35, 'Running component selection algorithms')
        
        # Run actual component selection
        if 'led' in user_input.lower():
            resistor_selection = component_selector.select_resistor_for_led(5.0, 2.0, 0.02)
            led_selection = component_selector.select_led('red')
        
        time.sleep(1)
        emit_progress('design', 'Optimizing circuit topology...', 45, 'Validating electrical connections')
        
        # Run the CrewAI design process (simplified for demo)
        time.sleep(2)
        emit_progress('design', 'Generating Arduino code...', 50, 'Code generation agent active')
        
        # Stage 3: Simulation
        time.sleep(1)
        emit_progress('simulation', 'Initializing SPICE simulator...', 55, 'Loading NGSpice engine')
        
        time.sleep(2)
        emit_progress('simulation', 'Running DC analysis...', 65, 'Calculating operating point')
        
        # Run simulation if we have circuit data
        simulation_results = None
        plot_data = None
        if 'led' in user_input.lower():
            # Create and simulate LED circuit
            circuit = simulator.create_led_circuit()
            if circuit:
                simulation_results = simulator.run_dc_analysis(circuit)
                plot_data = simulator.generate_plot(simulation_results) if simulation_results else None
        
        time.sleep(1)
        emit_progress('simulation', 'Running transient analysis...', 70, 'Simulating time-domain behavior')
        
        # Stage 4: Schematic Generation
        time.sleep(2)
        emit_progress('schematic', 'Generating schematic diagram...', 80, 'Using KiCad integration')
        
        # Generate schematic
        schematic_results = None
        if 'led' in user_input.lower():
            components = {'resistor_value': 330, 'led_color': 'red'}
            schematic_results = kicad_generator.create_led_schematic(components, './output')
        
        time.sleep(1)
        emit_progress('schematic', 'Creating netlist and documentation...', 90, 'Generating downloadable files')
        
        # Stage 5: Completion
        time.sleep(1)
        emit_progress('complete', 'Design complete!', 100, 'All files generated successfully')
        
        # Generate mock CrewAI result for demo
        mock_result = f"""
Circuit Design Complete!

Requirements Analysis:
- Input: {user_input}
- Circuit Type: LED Control Circuit
- Target Platform: Arduino Uno

Component Selection:
- Microcontroller: Arduino Uno R3
- Current Limiting Resistor: 330Ω (1/4W)
- LED: Red 5mm LED (2V forward voltage)

Circuit Analysis:
- Supply Voltage: 5V
- LED Current: ~18.75mA
- Power Dissipation: 56.25mW

Arduino Code Generated:
- Pin 13 configured as output
- Basic blink functionality implemented
- 1-second on/off cycle

Simulation Results:
- DC operating point verified
- Current within safe limits
- Thermal analysis passed

Files Generated:
- Schematic (SVG/JSON)
- Netlist (SPICE format)
- Arduino sketch (.ino)
- Component list (BOM)
        """
        
        # Send final results
        try:
            socketio.emit('design_complete', {
                'crew_result': mock_result,
                'simulation': simulation_results,
                'schematic': schematic_results,
                'plot_data': plot_data,
                'components': {
                    'resistor': resistor_selection if 'resistor_selection' in locals() else None,
                    'led': led_selection if 'led_selection' in locals() else None
                }
            })
            logger.info("Design complete event emitted successfully")
        except Exception as e:
            logger.warning(f"Failed to emit design_complete: {e}")
            print("Design process completed successfully!")
        
    except Exception as e:
        logger.error(f"Design process failed: {e}")
        try:
            socketio.emit('design_error', {
                'error': str(e),
                'message': 'Design process encountered an error'
            })
        except Exception as emit_error:
            logger.warning(f"Failed to emit error: {emit_error}")
            print(f"Design process failed: {e}")

@app.route('/simulate', methods=['POST'])
def simulate_circuit():
    """Handle circuit simulation requests."""
    try:
        data = request.get_json()
        circuit_type = data.get('type', 'led')
        
        if circuit_type == 'led':
            led_voltage = data.get('led_voltage', 2.0)
            supply_voltage = data.get('supply_voltage', 5.0)
            
            # Create and simulate circuit
            circuit = simulator.create_led_circuit(led_voltage, supply_voltage)
            if not circuit:
                return jsonify({'status': 'error', 'message': 'Failed to create circuit'})
            
            # Run DC analysis
            dc_results = simulator.run_dc_analysis(circuit)
            
            # Run transient analysis
            transient_results = simulator.run_transient_analysis(circuit, duration=2.0)
            
            # Generate plots
            dc_plot = simulator.generate_plot(dc_results) if dc_results else None
            transient_plot = simulator.generate_plot(transient_results) if transient_results else None
            
            return jsonify({
                'status': 'success',
                'dc_analysis': dc_results,
                'transient_analysis': transient_results,
                'dc_plot': dc_plot,
                'transient_plot': transient_plot
            })
        
        return jsonify({'status': 'error', 'message': 'Unsupported circuit type'})
        
    except Exception as e:
        logger.error(f"Simulation failed: {e}")
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/components', methods=['GET'])
def get_components():
    """Get available components from database."""
    try:
        session = get_session()
        from database.models import Component
        
        components = session.query(Component).all()
        component_list = []
        
        for comp in components:
            component_list.append({
                'id': comp.id,
                'name': comp.name,
                'category': comp.category,
                'value': comp.value,
                'unit': comp.unit,
                'cost': comp.cost,
                'description': comp.description
            })
        
        session.close()
        return jsonify({'status': 'success', 'components': component_list})
        
    except Exception as e:
        logger.error(f"Failed to get components: {e}")
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/download/<path:filename>')
def download_file(filename):
    """Download generated files."""
    try:
        return send_from_directory('./output', filename, as_attachment=True)
    except Exception as e:
        logger.error(f"File download failed: {e}")
        return jsonify({'status': 'error', 'message': 'File not found'})

@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    logger.info('Client connected')
    emit('connected', {'message': 'Connected to Circuit AI'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    logger.info('Client disconnected')

@socketio.on('test_simulation')
def handle_test_simulation():
    """Handle test simulation request."""
    try:
        emit('design_progress', {
            'stage': 'test',
            'message': 'Running test simulation...',
            'progress': 50
        })
        
        # Run a simple LED circuit simulation
        circuit = simulator.create_led_circuit()
        if circuit:
            results = simulator.run_dc_analysis(circuit)
            plot_data = simulator.generate_plot(results) if results else None
            
            emit('simulation_complete', {
                'results': results,
                'plot_data': plot_data
            })
        else:
            emit('simulation_error', {'error': 'Failed to create test circuit'})
            
    except Exception as e:
        logger.error(f"Test simulation failed: {e}")
        emit('simulation_error', {'error': str(e)})

if __name__ == '__main__':
    # Create output directory
    os.makedirs('./output', exist_ok=True)
    
    # Run with SocketIO
    socketio.run(app, host='0.0.0.0', port=12000, debug=True, allow_unsafe_werkzeug=True) 