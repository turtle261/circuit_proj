# AI-Powered Circuit Design Assistant

An AI-powered tool for automating circuit design, component selection, simulation, and Arduino code generation.

## Setup Instructions

1. Create a virtual environment:
```bash
python -m venv venv
```

2. Activate the virtual environment:
- Windows:
```bash
.\venv\Scripts\activate
```
- Unix/MacOS:
```bash
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Additional Requirements:
- KiCad (with Python scripting enabled)
- NGSpice (for PySpice)

## Project Structure

```
circuit_ai/
├── agents/           # AI agent implementations
├── ui/              # Flask web interface
├── database/        # Database models and migrations
├── simulations/     # Circuit simulation code
├── tests/           # Test files
└── utils/           # Utility functions
```

## Development Status

Currently in Phase 1: Core Infrastructure development. 