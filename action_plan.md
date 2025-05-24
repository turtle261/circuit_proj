# Action Plan: AI-Powered Circuit Design Assistant

This document outlines the actionable steps for implementing the development roadmap described in the `overview.md`.

## Phase 1: Core Infrastructure (Months 1–3)

**Objective:** Build a functional prototype with basic automation.

1.  **Project Setup:**
    *   Initialize a new Python project repository.
    *   Set up a virtual environment.
    *   Install core dependencies: `Flask`, `CrewAI`, `PySpice`, `SQLAlchemy` (for SQLite ORM), and `kicad-python` (or equivalent for KiCad API interaction).
    *   Configure project structure with directories for agents, UI, database, and simulations.

2.  **Component Database:**
    *   Define the schema for the SQLite component database (`components.db`).
    *   Include basic tables for component types (resistors, LEDs, etc.) and their key parameters (resistance, voltage, current, etc.).
    *   Implement basic data loading/seeding for a few common components.

3.  **CrewAI Agents - Basic Implementation:**
    *   Define the `ResearchAgent` role and task for parsing simple user inputs (e.g., "blink an LED").
    *   Define the `DesignAgent` role and task for generating a basic schematic.
    *   Implement the `ResearchAgent` to extract required components and basic topology from user input.
    *   Implement the `DesignAgent` using the KiCad Python API to:
        *   Place components (e.g., Arduino, LED, resistor).
        *   Create connections based on the research agent's output.
        *   Perform basic netlist generation.

4.  **Component Selection - Simplified:**
    *   Implement a basic heuristic-based component selection mechanism within the `DesignAgent` or a new `ComponentSelectionAgent`.
    *   For simple circuits (like blinking LED), use predefined or calculated values (e.g., calculate resistor for LED based on voltage and desired current).

5.  **Simulation - Basic DC Analysis:**
    *   Integrate `PySpice` to perform a basic DC bias point analysis on the generated schematic's netlist.
    *   Implement a task for the `SimulationAgent` to run this analysis.
    *   Add basic validation based on DC analysis results (e.g., check LED current).

6.  **Minimal Flask UI:**
    *   Set up a basic Flask application.
    *   Create a simple form for user text input (e.g., "design an LED blinker").
    *   Implement a backend endpoint to receive user input and trigger the CrewAI workflow.
    *   Display the output (e.g., text description of the generated circuit, a basic representation if possible).

7.  **Workflow Orchestration:**
    *   Set up the CrewAI process to orchestrate the `ResearchAgent`, `DesignAgent`, and `SimulationAgent` for simple circuit requests.

**Deliverable:** A functional prototype capable of generating simple schematics (like an LED circuit) from text input, performing basic DC simulation, and displaying a basic output.

## Phase 2: Enhanced Simulation and Code Generation (Months 4–6)

**Objective:** Expand functionality with robust simulation and code generation.

1.  **Enhanced SPICE Simulation:**
    *   Expand `PySpice` integration within the `SimulationAgent` to include:
        *   Transient analysis (essential for time-based circuits like blinking).
        *   AC analysis (for filter/amplifier circuits - potentially later in the phase).
        *   Monte Carlo analysis (basic implementation for component tolerance).
    *   Implement tasks to analyze and interpret results from these simulation types.
    *   Refine the iteration loop between `DesignAgent` and `SimulationAgent` for automatic schematic correction based on simulation failures.

2.  **Intelligent Component Selection (Thompson Sampling MVP):**
    *   Implement the foundational structure for Thompson Sampling.
    *   Store simulation results and potentially user feedback in the component database to update component performance models (e.g., Beta distribution parameters).
    *   Modify the `ComponentSelectionAgent` to use the Thompson Sampling algorithm for selecting components based on the models.
    *   Maintain the heuristic fallback for cases where Thompson Sampling data is insufficient.

3.  **Arduino Code Generation:**
    *   Define the `CodeGenerationAgent` role and task.
    *   Integrate a local or accessible LLM (e.g., Devstral-Small via API or local server).
    *   Implement the `CodeGenerationAgent` to:
        *   Take schematic data (pin assignments, component types) and user requirements as input.
        *   Generate clean, commented Arduino (.ino) code matching the circuit's functionality.
        *   Ensure pin assignments in code match the schematic.

4.  **Virtual Simulation Integration:**
    *   Investigate SimulIDE automation capabilities.
    *   If direct automation is feasible via command line or API, implement a task in the `SimulationAgent` to run basic Arduino sketches in SimulIDE and capture results/errors.
    *   If full automation is not feasible for the MVP, generate SimulIDE project files and provide clear manual instructions for the user to run the simulation.

5.  **Enhanced UI and Visualization:**
    *   Integrate Plotly with the Flask UI.
    *   Display generated schematics visually (requires generating image outputs from KiCad or a viewer).
    *   Display simulation results (e.g., voltage/current waveforms from transient analysis) using Plotly.
    *   Add real-time progress updates using WebSockets or AJAX to show the user which agent is working and its status.

6.  **Automated Documentation Generation:**
    *   Define the `DocumentationAgent` role and task.
    *   Implement the `DocumentationAgent` to:
        *   Gather outputs from other agents (schematic file, BOM data, simulation results, generated code).
        *   Compile these into a structured report (Markdown initially).
        *   Include assembly notes and basic troubleshooting based on the design and simulation.

**Deliverable:** A more robust prototype capable of performing transient simulations, generating functional Arduino code, integrating with a virtual simulator (manual or automated), displaying results visually, and generating a project report.

## Phase 3: Advanced Features and Polish (Months 7–9)

**Objective:** Deliver a polished, feature-rich platform.

1.  **Circuit Optimization ML Models:**
    *   Explore and implement simple machine learning models (potentially using libraries like scikit-learn or extending the Thompson Sampling approach) to suggest design improvements based on historical project data and simulation outcomes.
    *   Focus on optimizing key metrics like cost, power consumption, or component count.

2.  **Expanded KiCad Features:**
    *   Investigate and implement basic PCB layout assistance using the KiCad Python API. This could include:
        *   Basic component placement suggestions.
        *   Simple routing assistance.
    *   Explore supporting multi-sheet schematics or hierarchical designs for more complex projects.

3.  **Supplier API Integration:**
    *   Integrate with APIs from major suppliers (e.g., DigiKey, Mouser) to:
        *   Fetch real-time component availability and pricing data for the BOM.
        *   Update component information in the local database.
    *   Modify the `ComponentSelectionAgent` to consider real-time availability and pricing in its selection process (incorporating into the Thompson Sampling rewards).

4.  **Collaborative and Community Features:**
    *   Implement user accounts and project saving functionality.
    *   Add features for sharing projects with other users.
    *   Explore creating a mechanism for community-contributed component libraries or design templates.

5.  **User Testing and UI/UX Refinement:**
    *   Conduct structured user testing sessions with target hobbyists.
    *   Gather feedback on usability, clarity, and functionality.
    *   Iteratively refine the Flask UI/UX based on user feedback.
    *   Improve error handling and user guidance within the application.

6.  **Performance Optimization:**
    *   Profile the application to identify performance bottlenecks, especially in KiCad API interactions, simulations, and LLM calls.
    *   Optimize code for efficiency and reduce resource usage.
    *   Refine hardware requirements documentation and potentially explore options for running parts of the workflow on less powerful machines or offering optimized LLM configurations.

**Deliverable:** A production-ready, polished platform with advanced features, improved usability, supplier integration, and collaborative capabilities.

## General Guidelines
- **Testing**: Use tools like pytest for frequent, automated tests.
- **Debugging**: Employ logs and print statements to identify issues.
- **Version Control**: Commit changes regularly with descriptive messages.
- **MVP Completion**: Once all steps are done, the MVP should be a fully functional, open-source tool that's ready for deployment, user feedback, or acquisition talks—focusing on software excellence without fluff.

This streamlined plan keeps things at the software level, making it quick to follow and directly aimed at your MVP goals. If you need further tweaks or want to dive into specific implementations, just let me know! 