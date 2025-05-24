import subprocess
import logging
import os
from typing import Type
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

# Configure logging specifically for terminal commands
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
# Ensure handlers are not duplicated if this file is reloaded
if not logger.handlers:
    log_file_path = 'agent_terminal.log'
    # Create the log directory if it doesn't exist (optional, depends on desired log location)
    # log_dir = os.path.dirname(log_file_path)
    # if log_dir:
    #     os.makedirs(log_dir, exist_ok=True)
    file_handler = logging.FileHandler(log_file_path, mode='a')
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s: %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    # Optionally add a stream handler to see logs in the console as well
    # stream_handler = logging.StreamHandler()
    # stream_handler.setFormatter(formatter)
    # logger.addHandler(stream_handler)


class PowerShellToolInput(BaseModel):
    """Input schema for PowerShellTool."""
    command: str = Field(..., description="The PowerShell command to execute.")

class PowerShellTool(BaseTool):
    name: str = "PowerShell Terminal"
    description: str = (
        "Executes a given command in a PowerShell terminal and returns the output. "
        "Logs the command before execution to agent_terminal.log. "
        "Input should be a string containing the PowerShell command."
    )
    args_schema: Type[BaseModel] = PowerShellToolInput

    def _run(self, command: str) -> str:
        logger.info(f"Executing command: {command}")
        try:
            # Use subprocess.run to execute the command in PowerShell
            # shell=True is needed to run the command via the shell, which is PowerShell on Windows
            # capture_output=True captures stdout and stderr
            # text=True decodes stdout/stderr using default encoding
            # encoding='utf-8' can be specified for explicit decoding
            process = subprocess.run(
                ["powershell", "-Command", command],
                capture_output=True,
                text=True,
                encoding='utf-8', # Explicitly use utf-8
                check=True, # Raise CalledProcessError if the command returns a non-zero exit code
                shell=True # Needed to ensure powershell is found and command is interpreted correctly
            )
            output = process.stdout.strip()
            error_output = process.stderr.strip()

            if error_output:
                logger.warning(f"Command produced error output: {error_output}")
                return f"Command executed. Output:\n{output}\nError:\n{error_output}"
            else:
                logger.info("Command executed successfully.")
                return f"Command executed successfully. Output:\n{output}"

        except FileNotFoundError:
             logger.error("PowerShell executable not found. Is PowerShell installed and in the PATH?")
             return "Error: PowerShell executable not found. Please ensure PowerShell is installed and in your system's PATH."
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed with exit code {e.returncode}: {e.cmd}\nStderr: {e.stderr}\nStdout: {e.stdout}")
            return f"Error executing command (Exit Code {e.returncode}). Command: {e.cmd}\nOutput:\n{e.stdout}\nError:\n{e.stderr}"
        except Exception as e:
            logger.error(f"An unexpected error occurred during command execution: {e}", exc_info=True)
            return f"An unexpected error occurred: {str(e)}"
