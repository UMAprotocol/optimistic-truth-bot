#!/usr/bin/env python3
"""
Prompt refiner for UMA Optimistic Oracle.

This script analyzes incorrect predictions and uses ChatGPT to refine the system prompt. Used to make better Perplexity prompts.
"""

import json
import os
import sys
import time
import threading
from pathlib import Path
import concurrent.futures
import requests
from dotenv import load_dotenv
from openai import OpenAI

# Add the parent directory to the path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import setup_logging, spinner_animation
from prompt import PROMPT_VERSIONS, LATEST_VERSION

# Load environment variables
load_dotenv()

# Constants and configuration
API_KEY = os.getenv("OPENAI_API_KEY")
if not API_KEY:
    print("Error: OpenAI API key not found. Please set OPENAI_API_KEY in .env file.")
    sys.exit(1)

# Define paths
BASE_DIR = Path(__file__).parent  # combinatorial_follower directory
RESULTS_DIR = Path("proposal_replayer/results/14032025-gpt-refined-prompt/outputs")
OUTPUT_FILE = BASE_DIR / "refined_prompt.txt"

# Set up logging
logger = setup_logging("prompt_refiner", "prompt_refiner.log")

# Get the current system prompt
CURRENT_PROMPT = PROMPT_VERSIONS[LATEST_VERSION](
    int(time.time()), time.strftime("%Y-%m-%d %H:%M:%S")
)


def chat_completion(prompt):
    """Call the OpenAI API to get a completion."""
    # Create OpenAI client
    client = OpenAI(api_key=API_KEY)

    # Start spinner animation
    stop_event = threading.Event()
    spinner_thread = threading.Thread(
        target=spinner_animation, args=("Calling ChatGPT API...", stop_event)
    )
    spinner_thread.start()

    try:
        # Call the API
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=4000,
        )
        result = response.choices[0].message.content
    except Exception as e:
        logger.error(f"Error calling OpenAI API: {e}")
        result = f"Error: {e}"
    finally:
        # Stop spinner animation
        stop_event.set()
        spinner_thread.join()

    return result


def get_json_files():
    """Get a list of all JSON files in the results directory."""
    return list(RESULTS_DIR.glob("*.json"))


def save_refined_prompt(refined_prompt, filename="refined_prompt.txt"):
    # Extract just the filename, ignore any directory in the path
    _, basename = os.path.split(filename)
    
    # Define output directory path
    output_dir = Path("combinatorial_follower/overseer_prompt_output")
    output_dir.mkdir(exist_ok=True)
    
    # Use the filename in the output directory
    output_path = os.path.join(output_dir, basename)
    with open(output_path, "w") as f:
        f.write(refined_prompt)
    print(f"Refined prompt saved to {output_path}")


def main():
    """Main function."""
    logger.info("Starting prompt refinement process")

    # Get all JSON files
    json_files = get_json_files()
    logger.info(f"Found {len(json_files)} JSON files")

    # Load a sample of files for analysis
    sample_size = min(10, len(json_files))
    selected_files = json_files[:sample_size]
    logger.info(f"Selected {len(selected_files)} files for analysis")

    # Collect data from the JSON files
    data_samples = []
    for file_path in selected_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                data_samples.append(
                    {
                        "user_prompt": data.get("user_prompt", ""),
                        "system_prompt": data.get("system_prompt", ""),
                        "response": data.get("response", ""),
                        "recommendation": data.get("recommendation", ""),
                    }
                )
        except Exception as e:
            logger.error(f"Error loading {file_path}: {e}")

    # Create a prompt for ChatGPT to refine the system prompt
    refinement_prompt = f"""
You are a prompt engineering expert. I need your help to refine a system prompt used for an AI oracle that resolves prediction market questions.

Current system prompt:
{CURRENT_PROMPT}

Here are some examples of user prompts, the system prompt, and the AI's responses:

{json.dumps(data_samples, indent=2)}

Based on these examples, please analyze the prompt and suggest improvements. Consider:
1. Are there any unclear instructions that could be clarified?
2. Are there any missing instructions that would improve response quality?
3. Are there any patterns of errors or misconceptions that could be addressed?
4. How could the prompt be restructured to be more effective?

Provide a complete, refined version of the system prompt that addresses these issues.
"""

    # Call ChatGPT to refine the prompt
    logger.info("Calling ChatGPT to refine prompt")
    refined_prompt = chat_completion(refinement_prompt)
    logger.info("Received refined prompt from ChatGPT")

    # Save the refined prompt
    save_refined_prompt(refined_prompt)


if __name__ == "__main__":
    main()
