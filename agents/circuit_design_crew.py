"""
Circuit Design Crew - Main orchestration for the AI-powered circuit design assistant.
"""
import os
import logging
from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from crewai.memory import ShortTermMemory, EntityMemory, LongTermMemory
from crewai.memory.contextual.contextual_memory import ContextualMemory
from crewai.memory.storage.ltm_sqlite_storage import LTMSQLiteStorage
from crewai.memory.storage.rag_storage import RAGStorage
import google.generativeai as genai
from dotenv import load_dotenv
import yaml

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s: %(message)s',
        handlers=[logging.FileHandler('circuit_design.log', mode='a'), logging.StreamHandler()]
    )

# Environment setup
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MEMORY_BASE_PATH = os.getenv("MEMORY_BASE_PATH", "./memory")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is required")

# Configure Gemini
try:
    genai.configure(api_key=GEMINI_API_KEY)
except Exception as e:
    logger.error(f"Failed to configure Gemini: {e}")
    raise

# Memory setup
os.makedirs(f"{MEMORY_BASE_PATH}/short_term", exist_ok=True)
os.makedirs(f"{MEMORY_BASE_PATH}/entity", exist_ok=True)
os.makedirs(f"{MEMORY_BASE_PATH}/long_term", exist_ok=True)

# Initialize storage for long-term memory using SQLite
ltm_storage = LTMSQLiteStorage(
    db_path=f"{MEMORY_BASE_PATH}/long_term/ltm.db",
)

# Initialize RAGStorages for ShortTermMemory and EntityMemory
embedder_config = {
    "provider": "google",
    "config": {
        "api_key": GEMINI_API_KEY,
        "model": "models/text-embedding-004",
        "task_type": "retrieval_document"
    }
}

rag_stm_storage = RAGStorage(
    embedder_config=embedder_config,
    type="short_term",
    path=f"{MEMORY_BASE_PATH}/short_term"
)

rag_em_storage = RAGStorage(
    embedder_config=embedder_config,
    type="entity",
    path=f"{MEMORY_BASE_PATH}/entity"
)

# Initialize CrewAI Memory Components
crew_short_term_memory = ShortTermMemory(storage=rag_stm_storage)
crew_entity_memory = EntityMemory(storage=rag_em_storage)
crew_long_term_memory = LongTermMemory(storage=ltm_storage)
global_contextual_memory = ContextualMemory(
    stm=crew_short_term_memory,
    em=crew_entity_memory,
    ltm=crew_long_term_memory, 
    memory_config=None, 
    um=None, 
    exm=None
)

@CrewBase
class CircuitDesignCrew:
    """Circuit Design Crew for AI-powered circuit design assistant."""
    
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'
    
    def __init__(self):
        # Load configurations
        config_dir = os.path.join(os.path.dirname(__file__), 'config')
        
        with open(os.path.join(config_dir, 'agents.yaml'), 'r') as f:
            self.agents_config = yaml.safe_load(f)
        
        with open(os.path.join(config_dir, 'tasks.yaml'), 'r') as f:
            self.tasks_config = yaml.safe_load(f)
    
    def _create_llm(self):
        """Create Gemini LLM instance."""
        return LLM(
            model="gemini/gemini-2.0-flash-exp",
            api_key=GEMINI_API_KEY,
            max_tokens=8192,
        )
    
    @agent
    def research_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['research_agent'],
            llm=self._create_llm(),
            verbose=True,
            max_rpm=10,
            max_iter=5,
            memory=True,
            respect_context_window=True,
            cache=True,
        )
    
    @agent
    def design_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['design_agent'],
            llm=self._create_llm(),
            verbose=True,
            max_rpm=10,
            max_iter=5,
            memory=True,
            respect_context_window=True,
            cache=True,
        )
    
    @agent
    def component_selection_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['component_selection_agent'],
            llm=self._create_llm(),
            verbose=True,
            max_rpm=10,
            max_iter=5,
            memory=True,
            respect_context_window=True,
            cache=True,
        )
    
    @agent
    def simulation_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['simulation_agent'],
            llm=self._create_llm(),
            verbose=True,
            max_rpm=10,
            max_iter=5,
            memory=True,
            respect_context_window=True,
            cache=True,
        )
    
    @agent
    def code_generation_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['code_generation_agent'],
            llm=self._create_llm(),
            verbose=True,
            max_rpm=10,
            max_iter=5,
            memory=True,
            respect_context_window=True,
            cache=True,
        )
    
    @agent
    def documentation_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['documentation_agent'],
            llm=self._create_llm(),
            verbose=True,
            max_rpm=10,
            max_iter=5,
            memory=True,
            respect_context_window=True,
            cache=True,
        )
    
    @task
    def research_task(self) -> Task:
        return Task(
            config=self.tasks_config['research_task'],
            agent=self.research_agent(),
        )
    
    @task
    def design_task(self) -> Task:
        return Task(
            config=self.tasks_config['design_task'],
            agent=self.design_agent(),
        )
    
    @task
    def component_selection_task(self) -> Task:
        return Task(
            config=self.tasks_config['component_selection_task'],
            agent=self.component_selection_agent(),
        )
    
    @task
    def simulation_task(self) -> Task:
        return Task(
            config=self.tasks_config['simulation_task'],
            agent=self.simulation_agent(),
        )
    
    @task
    def code_generation_task(self) -> Task:
        return Task(
            config=self.tasks_config['code_generation_task'],
            agent=self.code_generation_agent(),
        )
    
    @task
    def documentation_task(self) -> Task:
        return Task(
            config=self.tasks_config['documentation_task'],
            agent=self.documentation_agent(),
        )
    
    @crew
    def crew(self) -> Crew:
        """Creates the Circuit Design crew"""
        return Crew(
            agents=[
                self.research_agent(),
                self.design_agent(),
                self.component_selection_agent(),
                self.simulation_agent(),
                self.code_generation_agent(),
                self.documentation_agent()
            ],
            tasks=[
                self.research_task(),
                self.design_task(),
                self.component_selection_task(),
                self.simulation_task(),
                self.code_generation_task(),
                self.documentation_task()
            ],
            process=Process.sequential,
            contextual_memory=global_contextual_memory,
            verbose=True,
            max_rpm=10
        )

def run_circuit_design(user_input: str):
    """Run the circuit design process with user input."""
    try:
        crew_instance = CircuitDesignCrew()
        crew = crew_instance.crew()
        
        # Execute the crew with user input
        result = crew.kickoff(inputs={'user_input': user_input})
        
        return result
    except Exception as e:
        logger.error(f"Error running circuit design crew: {e}")
        # Return a fallback result instead of raising to keep the system working
        return f"Circuit Design Analysis for: {user_input}\n\nNote: AI agents encountered an issue ({str(e)[:100]}...), but the system will continue with component selection and simulation." 