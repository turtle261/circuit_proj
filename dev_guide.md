# Circuit AI Development Guide

## Overview
This guide provides comprehensive instructions for setting up the development environment for the AI-powered circuit design assistant, including all dependencies required for Phase 2.1 advanced simulation capabilities.

## System Requirements

### Operating System
- Ubuntu 20.04+ (recommended)
- Debian 11+ 
- Other Linux distributions with package manager support

### Hardware Requirements
- Minimum 4GB RAM (8GB recommended for Monte Carlo simulations)
- 2+ CPU cores
- 2GB free disk space
- Internet connection for package downloads

## Dependencies Installation

### 1. System Package Dependencies

```bash
# Update package manager
sudo apt update && sudo apt upgrade -y

# Install Python and development tools
sudo apt install -y python3 python3-pip python3-venv python3-dev

# Install NGSpice (SPICE circuit simulator)
sudo apt install -y ngspice libngspice0-dev

# Install KiCad (schematic capture and PCB design)
sudo apt install -y kicad kicad-libraries

# Install additional system libraries
sudo apt install -y build-essential cmake git curl wget
sudo apt install -y libffi-dev libssl-dev libxml2-dev libxslt1-dev
sudo apt install -y libjpeg-dev libpng-dev libfreetype6-dev

# Install Node.js (for frontend dependencies if needed)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
```

### 2. NGSpice Configuration

```bash
# Verify NGSpice installation
ngspice --version

# Create symbolic link for PySpice compatibility
sudo ln -sf /usr/lib/x86_64-linux-gnu/libngspice.so.0 /usr/lib/x86_64-linux-gnu/libngspice.so

# Test NGSpice shared library
python3 -c "
import ctypes
try:
    lib = ctypes.CDLL('libngspice.so')
    print('✓ NGSpice shared library loaded successfully')
except Exception as e:
    print(f'✗ NGSpice library error: {e}')
"
```

### 3. Python Environment Setup

```bash
# Create virtual environment
python3 -m venv circuit_ai_env
source circuit_ai_env/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel

# Install core Python dependencies
pip install -r requirements.txt

# Alternative manual installation if requirements.txt is not available:
pip install flask flask-socketio
pip install crewai crewai-tools
pip install PySpice
pip install sqlalchemy
pip install plotly matplotlib numpy scipy
pip install python-dotenv eventlet
pip install requests beautifulsoup4
```

### 4. Environment Variables

Create a `.env` file in the project root:

```bash
# Copy example environment file
cp .env.example .env

# Edit with your API keys
nano .env
```

Required environment variables:
```env
# Gemini API Key for CrewAI agents
GEMINI_API_KEY=your_gemini_api_key_here

# Optional: OpenAI API Key (alternative to Gemini)
OPENAI_API_KEY=your_openai_api_key_here

# Flask configuration
FLASK_ENV=development
FLASK_DEBUG=True

# Database configuration
DATABASE_URL=sqlite:///circuit_ai.db
```

### 5. Database Setup

```bash
# Initialize database
python3 -c "
from database.models import create_database
from database.seed_data import seed_basic_components
create_database()
seed_basic_components()
print('✓ Database initialized successfully')
"
```

## Verification and Testing

### 1. Dependency Verification

Run the comprehensive dependency check:

```bash
python3 -c "
import sys
import importlib

dependencies = [
    'flask', 'flask_socketio', 'crewai', 'PySpice', 
    'sqlalchemy', 'plotly', 'matplotlib', 'numpy', 
    'scipy', 'dotenv', 'eventlet', 'requests'
]

print('Checking Python dependencies...')
for dep in dependencies:
    try:
        importlib.import_module(dep)
        print(f'✓ {dep}')
    except ImportError:
        print(f'✗ {dep} - MISSING')

# Check NGSpice
try:
    from PySpice.Spice.NgSpice.Shared import NgSpiceShared
    ngspice = NgSpiceShared.new_instance()
    print('✓ NGSpice integration working')
except Exception as e:
    print(f'✗ NGSpice integration failed: {e}')

# Check KiCad
import subprocess
try:
    result = subprocess.run(['kicad-cli', '--version'], capture_output=True, text=True)
    if result.returncode == 0:
        print('✓ KiCad CLI available')
    else:
        print('⚠ KiCad CLI not available (GUI-only installation)')
except FileNotFoundError:
    print('⚠ KiCad not found in PATH')
"
```

### 2. Phase 2.1 Feature Testing

```bash
# Run basic Phase 2.1 tests
python3 test_phase_2_1.py

# Run CrewAI integration tests
python3 test_crewai_phase_2_1.py

# Run integration tests
python3 test_phase_2_1_integration.py

# Run advanced feature tests
python3 test_phase_2_1_advanced.py
```

### 3. Flask Application Testing

```bash
# Start the Flask development server
export GEMINI_API_KEY=your_api_key_here
python3 ui/app.py

# In another terminal, test the API
curl -X GET http://localhost:12000/
curl -X POST http://localhost:12000/api/design \
  -H "Content-Type: application/json" \
  -d '{"description": "Design a simple LED circuit"}'
```

## Development Workflow

### 1. Project Structure

```
circuit_proj/
├── agents/                 # CrewAI agents and tools
│   ├── circuit_design_crew.py
│   └── tools/
│       └── advanced_simulation_tool.py
├── database/              # Database models and seed data
│   ├── models.py
│   └── seed_data.py
├── simulations/           # SPICE simulation engine
│   └── spice_simulator.py
├── ui/                    # Flask web interface
│   ├── app.py
│   └── templates/
├── utils/                 # Utility modules
│   ├── component_selection.py
│   └── kicad_integration.py
├── test_*.py             # Test suites
├── requirements.txt      # Python dependencies
├── .env                  # Environment variables
└── dev_guide.md         # This file
```

### 2. Adding New Circuit Types

1. **Update Circuit Simulator** (`simulations/spice_simulator.py`):
   ```python
   def create_new_circuit_type(self, parameters):
       # Implement circuit creation logic
       pass
   ```

2. **Update Advanced Simulation Tool** (`agents/tools/advanced_simulation_tool.py`):
   ```python
   def _create_circuit(self, circuit_type, parameters):
       if circuit_type == 'new_type':
           return self.simulator.create_new_circuit_type(parameters)
   ```

3. **Add Test Cases** (`test_phase_2_1.py`):
   ```python
   def test_new_circuit_type(self):
       # Implement test logic
       pass
   ```

### 3. Debugging Common Issues

#### NGSpice Library Issues
```bash
# Check library path
ldconfig -p | grep ngspice

# Fix missing library
sudo apt install --reinstall libngspice0-dev
sudo ldconfig
```

#### PySpice Import Errors
```bash
# Reinstall PySpice
pip uninstall PySpice
pip install PySpice --no-cache-dir
```

#### CrewAI API Issues
```bash
# Verify API key
echo $GEMINI_API_KEY

# Test API connectivity
python3 -c "
import os
from crewai import Agent
agent = Agent(
    role='test',
    goal='test connection',
    backstory='test',
    llm='gemini/gemini-pro'
)
print('✓ CrewAI API connection working')
"
```

## Performance Optimization

### 1. Simulation Performance

- **Monte Carlo Analysis**: Reduce iterations for development (50-100), increase for production (1000+)
- **AC Analysis**: Limit frequency range and points per decade for faster execution
- **Temperature Analysis**: Use coarser temperature steps during development

### 2. Memory Management

```python
# For large Monte Carlo simulations
import gc
gc.collect()  # Force garbage collection between iterations
```

### 3. Parallel Processing

```python
# Enable parallel processing for Monte Carlo
from multiprocessing import Pool
# Implement parallel circuit generation
```

## Production Deployment

### 1. Environment Setup

```bash
# Production environment variables
export FLASK_ENV=production
export FLASK_DEBUG=False

# Use production WSGI server
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 ui.app:app
```

### 2. Database Migration

```bash
# Backup development database
cp circuit_ai.db circuit_ai_backup.db

# Run production database setup
python3 database/models.py
```

### 3. Monitoring and Logging

```python
# Configure production logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('circuit_ai.log'),
        logging.StreamHandler()
    ]
)
```

## Troubleshooting

### Common Error Messages

1. **"libngspice.so: cannot open shared object file"**
   - Solution: Install NGSpice development libraries and create symbolic link

2. **"Unsupported Ngspice version"**
   - Solution: This is a warning, not an error. NGSpice v39+ is supported

3. **"Command 'run' failed" in AC analysis**
   - Solution: Check circuit DC bias points and AC source configuration

4. **CrewAI API timeout errors**
   - Solution: Check internet connection and API key validity

### Getting Help

1. **Check logs**: Review application logs for detailed error messages
2. **Run tests**: Execute test suites to identify specific issues
3. **Verify dependencies**: Ensure all required packages are installed
4. **Check documentation**: Review Phase 2.1 specifications in `phase_two_deep.md`

## Version Information

- **NGSpice**: v39.3+ (tested with v39.3)
- **Python**: 3.8+ (tested with 3.12)
- **KiCad**: v6.0+ (tested with v6.0.11)
- **Flask**: v2.0+
- **CrewAI**: Latest stable version

## License and Contributing

This project is part of the Circuit AI system. See the main project documentation for licensing and contribution guidelines.

---

**Last Updated**: 2025-05-24  
**Version**: Phase 2.1  
**Maintainer**: Circuit AI Development Team