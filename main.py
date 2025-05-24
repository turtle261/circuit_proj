"""
Main entry point for the Circuit Design Assistant.
"""
import os
import logging
from dotenv import load_dotenv
from database.models import create_database
from database.seed_data import seed_basic_components
from agents.circuit_design_crew import run_circuit_design

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('circuit_design.log', mode='a'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def initialize_database():
    """Initialize the database and seed basic components."""
    try:
        create_database()
        seed_basic_components()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

def main():
    """Main entry point for the Circuit Design Assistant."""
    try:
        # Initialize database
        initialize_database()
        
        print("\nWelcome to the Circuit Design Assistant!")
        print("I can help you design Arduino circuits and generate code.")
        print("Type 'exit' to quit.\n")
        
        while True:
            user_input = input("What kind of circuit would you like to design? ")
            
            if user_input.lower() == 'exit':
                print("\nThank you for using the Circuit Design Assistant!")
                break
            
            try:
                print("\nDesigning your circuit... This may take a few minutes.\n")
                result = run_circuit_design(user_input)
                print("\nCircuit Design Results:")
                print(result)
                print("\nWhat else would you like to design?")
            except Exception as e:
                logger.error(f"Error processing user input: {e}")
                print(f"\nSorry, I encountered an error: {e}")
                print("Please try again with a different description.")
    
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise

if __name__ == "__main__":
    main() 