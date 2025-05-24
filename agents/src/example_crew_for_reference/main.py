#!/usr/bin/env python
import sys
import warnings
import time
import os

from example_crew_for_reference.crew import Onito
from dotenv import load_dotenv

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# Load environment variables
load_dotenv()

# This main file is intended to be a way for you to run your
# crew locally, so refrain from adding unnecessary logic into this file.
# Replace with inputs you want to test with, it will automatically
# interpolate any tasks and agents information

def run():
    """
    Run the crew with user-provided inputs.
    """
    # Get user input for the topic/message
    current_message = input("Enter your query/topic: ").strip()
    if not current_message:
        print("Error: Query/topic cannot be empty.")
        return

    # Optional: Get user ID and session ID (or generate defaults)
    # user_id = input("Enter user ID (leave empty for default): ").strip() or "default_user"
    # session_id = input("Enter session ID (leave empty for auto-generated): ").strip() or f"session_{user_id}_{int(time.time())}"

    # Prepare inputs
    inputs = {
        # 'user_id': user_id,
        # 'session_id': session_id,
        'current_message': current_message
    }

    # Run the crew
    result = Onito().crew().kickoff(inputs=inputs)
    print(result)

def train():
    """
    Train the crew with user-provided inputs.
    """
    topic = input("Enter training topic: ").strip()
    if not topic:
        print("Error: Training topic cannot be empty.")
        return

    iterations_input = input("Enter number of iterations (default: 1): ").strip() or "1"
    try:
        iterations = int(iterations_input)
        if iterations <= 0:
            print("Error: Number of iterations must be a positive integer.")
            return  # Explicit check as per documentation
    except ValueError:
        print("Error: Number of iterations must be a valid integer.")
        return

    filename = input("Enter output filename (default: training_output.pkl): ").strip() or "training_output.pkl"
    if not filename.endswith('.pkl'):
        print("Error: Filename must end with '.pkl' as per documentation requirements.")
        return  # Explicit check to ensure filename compliance

    inputs = {
        "current_message": topic
    }
    try:
        Onito().crew().train(n_iterations=iterations, filename=filename, inputs=inputs)
    except Exception as e:
        print(f"An error occurred while training the crew: {e}")

def replay():
    """
    Replay the crew execution from a specific task.
    """
    task_id = input("Enter task ID to replay: ").strip()
    if not task_id:
        print("Error: Task ID cannot be empty.")
        return

    try:
        Onito().crew().replay(task_id=task_id)
    except Exception as e:
        print(f"An error occurred while replaying the crew: {e}")

def test():
    """
    Test the crew execution with user-provided inputs.
    """
    topic = input("Enter test topic: ").strip()
    if not topic:
        print("Error: Test topic cannot be empty.")
        return

    iterations = input("Enter number of iterations (default: 1): ").strip() or "1"
    model_name = input("Enter OpenAI model name (default: gemini/gemini-2.5-flash-preview-04-17): ").strip() or "gemini/gemini-2.5-flash-preview-04-17"

    inputs = {
        "topic": topic
    }
    try:
        Onito().crew().test(n_iterations=int(iterations), openai_model_name=model_name, inputs=inputs)
    except Exception as e:
        print(f"An error occurred while testing the crew: {e}")

if __name__ == "__main__":
    print("Select an action:")
    print("1. Run the crew")
    print("2. Train the crew")
    print("3. Replay a task")
    print("4. Test the crew")
    choice = input("Enter your choice (1-4): ").strip()

    if choice == "1":
        run()
    elif choice == "2":
        train()
    elif choice == "3":
        replay()
    elif choice == "4":
        test()
    else:
        print("Invalid choice. Exiting.")
