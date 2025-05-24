import os
import logging
import mlflow # Import MLflow
import mlflow.crewai # Import MLflow CrewAI autolog
from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from crewai.memory import ShortTermMemory, EntityMemory, LongTermMemory
from crewai.memory.contextual.contextual_memory import ContextualMemory
from crewai.memory.storage.ltm_sqlite_storage import LTMSQLiteStorage
from crewai.memory.storage.rag_storage import RAGStorage
from crewai_tools import FileReadTool, FileWriterTool, DirectoryReadTool, DirectorySearchTool, CodeDocsSearchTool, CodeInterpreterTool
import litellm
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Enable debugging
litellm._turn_on_debug()

# Configure logging
logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s: %(message)s',
        handlers=[logging.FileHandler('agent.log', mode='a'), logging.StreamHandler()]
    )

# Environment setup
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "mock_key_for_testing")
#LLM_MODEL = os.getenv("LLM_MODEL", "gemini/gemini-2.5-flash-preview-04-17")
MEMORY_BASE_PATH = os.getenv("MEMORY_BASE_PATH", "./memory")
# Add OpenRouter API Key loading
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Always configure Gemini
#try:
#    genai.configure(api_key=GEMINI_API_KEY)
#except Exception as e:
#    logger.error(f"Failed to configure Gemini: {e}")
#    # Decide if you want to raise or handle differently
    # raise

# Optional: Set a tracking URI and an experiment name if you have a tracking server

# --- ChromaDB Setup ---
# Create directories for memory storage
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
        "model": "models/gemini-embedding-exp-03-07",
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
    ltm=crew_long_term_memory, memory_config=None, um=None, exm=None
)

# --- Tool Initialization ---
# Initialize tools with default settings for dynamic use
file_read_tool = FileReadTool()
file_writer_tool = FileWriterTool()
directory_read_tool = DirectoryReadTool()
directory_search_tool = DirectorySearchTool()
codedocs_search_tool = CodeDocsSearchTool()
code_interpreter_tool = CodeInterpreterTool() # Initialize CodeInterpreterTool

# Import custom web tools
from .tools.web_tools import HyperBrowserToolWrapper, HyperScrapeToolWrapper, HyperCrawlToolWrapper, HyperExtractToolWrapper

hyperbrowser_tool = HyperBrowserToolWrapper()
hyper_scrape_tool = HyperScrapeToolWrapper()
hyper_crawl_tool = HyperCrawlToolWrapper()
hyper_extract_tool = HyperExtractToolWrapper()

# List of tools to provide to the agent
agent_tools = [
    file_read_tool,
    file_writer_tool,
    directory_read_tool,
    directory_search_tool,
    codedocs_search_tool,
    hyperbrowser_tool,
    hyper_scrape_tool,
    hyper_crawl_tool,
    hyper_extract_tool,
    code_interpreter_tool
]

# Define the LLM for function calling
function_calling_llm = LLM(
    model="openrouter/mistralai/devstral-small:free",
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY # From .env
)


@CrewBase
class Onito():
	"""Onito crew"""

	agents_config = 'config/agents.yaml'
	tasks_config = 'config/tasks.yaml'

	@agent
	def polymath(self) -> Agent:
		return Agent(
			config=self.agents_config['polymath'],
			llm=LLM(
                model="gemini/gemini-2.5-flash-preview-04-17",
                api_key=GEMINI_API_KEY,
                max_tokens=65536,
            ),
			verbose=True,
			max_rpm=2,
			max_iter=100,
			memory=True,
			respect_context_window=True,
			cache=True,
			tools=agent_tools,
			max_retry_limit=32
		)

	@task
	def polymath_task(self) -> Task:
		return Task(
			config=self.tasks_config['polymath_task'],
		)

	@crew
	def crew(self) -> Crew:
		"""Creates the Onito crew"""
		return Crew(
			agents=[self.polymath()], # Use the polymath agent
			tasks=[self.polymath_task()], # Use the polymath task
			process=Process.sequential,
			contextual_memory=global_contextual_memory, # Use the globally initialized contextual memory
			verbose=True,
            # Add the function calling LLM
            function_calling_llm=function_calling_llm,
            # Crew-level retry/timeout settings could also be relevant,
            # but agent/LLM level is more direct for API calls
			max_rpm=5
		)
