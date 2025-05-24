# Circuit Design Assistant

An AI-powered assistant for designing Arduino circuits and generating code. This tool uses a crew of specialized AI agents to help you design, simulate, and document electronic circuits.

## Features

- Circuit design and analysis
- Component selection and optimization
- SPICE simulation
- Arduino code generation
- Comprehensive documentation
- Performance tracking and feedback

## Prerequisites

- Python 3.8 or higher
- Google Gemini API key

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/circuit_ai.git
cd circuit_ai
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root with your Gemini API key:
```
GEMINI_API_KEY=your_api_key_here
```

## Usage

1. Run the main script:
```bash
python main.py
```

2. Follow the prompts to describe the circuit you want to design.

3. The assistant will:
   - Analyze your requirements
   - Design the circuit
   - Select appropriate components
   - Simulate the circuit
   - Generate Arduino code
   - Create documentation

## Project Structure

```
circuit_ai/
├── agents/
│   ├── config/
│   │   ├── agents.yaml
│   │   └── tasks.yaml
│   └── circuit_design_crew.py
├── database/
│   ├── models.py
│   └── seed_data.py
├── main.py
├── requirements.txt
└── README.md
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- CrewAI for the agent orchestration framework
- Google Gemini for the AI capabilities
- SQLAlchemy for database management 