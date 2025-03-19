#!/usr/bin/env python3
"""
Prompt refiner for UMA Optimistic Oracle.

This script analyzes incorrect predictions and uses ChatGPT to refine the system prompt.
"""

import json
import os
import sys
import time
import threading
from pathlib import Path
import concurrent.futures
from dotenv import load_dotenv

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

BASE_DIR = Path(__file__).parent
RESULTS_DIR = (
    BASE_DIR
    / "proposal_replayer"
    / "combinatorial_follower"
    / "results"
    / "14032025-gpt-refined-prompt"
    / "outputs"
)
OUTPUT_FILE = BASE_DIR / "refined_prompt.txt"

# Set up logging
logger = setup_logging("prompt_refiner", "prompt_refiner.log")

# Get the current system prompt
CURRENT_PROMPT = PROMPT_VERSIONS[LATEST_VERSION](
    int(time.time()), time.strftime("%Y-%m-%d %H:%M:%S")
)


def chat_completion(prompt):
    """Call the OpenAI API to get a completion."""
    from openai import OpenAI

    client = OpenAI(api_key=API_KEY)

    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {
                "role": "system",
                "content": "You are an expert prompt engineer. Your job is to refine a system prompt based on examples of incorrect predictions. ONLY return the refined prompt without any additional comments, explanations or formatting.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
    )

    return response.choices[0].message.content


def get_json_files():
    """Get all JSON files from the output directory."""
    return list(RESULTS_DIR.glob("*.json"))


def process_file(file_path):
    """Process a single file and return a query for ChatGPT if needed."""
    try:
        with open(file_path, "r") as f:
            data = json.load(f)

        recommendation = data.get("recommendation")
        proposed_price_outcome = data.get("proposed_price_outcome")

        # Check if the recommendation doesn't match the proposed price outcome
        if recommendation != proposed_price_outcome:
            # Build the query for ChatGPT
            query = f"""
I need to refine a system prompt for an AI oracle that's used to resolve prediction market questions. 
The current prompt doesn't handle certain cases correctly.

CURRENT SYSTEM PROMPT:
{CURRENT_PROMPT}

Here's an example where the model produced incorrect results:

USER PROMPT:
{data.get('user_prompt')}

MODEL RESPONSE:
{data.get('response')}

MODEL RECOMMENDATION: {recommendation}
CORRECT OUTCOME: {proposed_price_outcome}

The model should have given the outcome {proposed_price_outcome} instead of {recommendation}.

Please refine the system prompt to address this issue. Return ONLY the refined prompt without any explanation or additional text.
"""
            return query
        return None
    except Exception as e:
        logger.error(f"Error processing {file_path.name}: {str(e)}")
        return None


def main():
    """Main function to refine the prompt."""
    json_files = get_json_files()
    total_files = len(json_files)
    processed = 0
    incorrect_predictions = 0
    refinement_queries = []

    print(f"\nFound {total_files} JSON files to process")
    print("\nProcessing files:")
    print("=" * 80)

    # Process all files and collect refinement queries
    for file_path in json_files:
        query = process_file(file_path)
        if query:
            refinement_queries.append(query)
            incorrect_predictions += 1

        # Update progress
        processed += 1
        progress = int(50 * processed / total_files)
        sys.stdout.write(
            f"\r[{'=' * progress}{' ' * (50 - progress)}] {processed}/{total_files} ({processed/total_files:.1%})"
        )
        sys.stdout.flush()

    print(
        f"\n\nFound {incorrect_predictions} incorrect predictions out of {total_files} files"
    )

    if incorrect_predictions == 0:
        print("\nNo incorrect predictions found. No refinement needed.")
        return

    print("\nGenerating refined prompt...")

    # Ask ChatGPT to refine the prompt based on all incorrect predictions
    refined_prompt = CURRENT_PROMPT

    for i, query in enumerate(refinement_queries):
        print(f"\nProcessing refinement {i+1}/{len(refinement_queries)}")

        # Show spinner while waiting for API response
        stop_event = threading.Event()
        spinner_thread = threading.Thread(
            target=spinner_animation,
            args=(stop_event, f"Processing refinement {i+1}/{len(refinement_queries)}"),
        )
        spinner_thread.start()

        try:
            new_prompt = chat_completion(query)
            if new_prompt:
                refined_prompt = new_prompt
        finally:
            stop_event.set()
            spinner_thread.join()

    # Save the refined prompt to a file
    with open(OUTPUT_FILE, "w") as f:
        f.write(refined_prompt)

    print(f"\nRefined prompt saved to {OUTPUT_FILE}")
    print("\nFinal refined prompt:")
    print("=" * 80)
    print(refined_prompt)
    print("=" * 80)


if __name__ == "__main__":
    main()
