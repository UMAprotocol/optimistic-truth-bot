#!/usr/bin/env python3
"""
Example script demonstrating how to query the Perplexity API with sample Optimistic Oracle queries.

This script shows the simplest possible Perplexity query implementation. It loads sample queries,
processes them with the Perplexity API, and saves the results to JSON files.

Usage:
    python example/example.py
"""

from dotenv import load_dotenv
import os
import json
import sys
import threading
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import query_perplexity, extract_recommendation, spinner_animation

print(
    "🔮 Running sample entry point to query perplexity directly against known questions 🤖 🔍"
)

load_dotenv()

PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")


def process_and_query(query_data, api_key):
    prompt = f"\n\nancillary_data:\n{query_data.ancillary_data}\n\nresolution_conditions:\n{query_data.resolution_conditions}\n\nupdates:\n{query_data.updates}"

    # Start spinner animation
    stop_spinner = threading.Event()
    spinner_message = f"Querying Perplexity API for {query_data.query_id[:8]}"
    spinner_thread = threading.Thread(
        target=spinner_animation, args=(stop_spinner, spinner_message)
    )
    spinner_thread.daemon = True
    spinner_thread.start()

    try:
        return query_perplexity(prompt, api_key, verbose=True)
    finally:
        # Stop the spinner animation
        stop_spinner.set()
        spinner_thread.join()


def query_all_samples(api_key):
    from sample_OO_queries import queries

    return [(query, process_and_query(query, api_key)) for query in queries]


def save_results_to_json(results):
    """Save or append results to a JSON file."""
    # Create the results directory if it doesn't exist
    os.makedirs("results", exist_ok=True)

    # Prepare the data structure for this run
    timestamp = datetime.now().isoformat()
    result_data = {"execution_time": timestamp, "queries": []}

    for query, response in results:
        recommendation = extract_recommendation(response.choices[0].message.content)
        result_data["queries"].append(
            {"query_id": query.query_id, "recommendation": recommendation}
        )

    # File path
    file_path = "results/direct_defined_queries.json"

    # Load existing data if file exists
    existing_data = []
    if os.path.exists(file_path):
        try:
            with open(file_path, "r") as f:
                existing_data = json.load(f)
        except json.JSONDecodeError:
            # Handle case where file exists but is empty or corrupted
            existing_data = []

    # Append new data
    if isinstance(existing_data, list):
        existing_data.append(result_data)
    else:
        existing_data = [result_data]

    # Write back to file
    with open(file_path, "w") as f:
        json.dump(existing_data, f, indent=2)

    print(f"Results saved to {file_path}")


if __name__ == "__main__":
    results = query_all_samples(PERPLEXITY_API_KEY)

    # Save results to JSON
    save_results_to_json(results)

    # Display results as before
    for i, (query, response) in enumerate(results):
        print(f"\n{'='*80}")
        print(f"Query {i+1} Response:")
        print(f"{'='*80}")
        print(f"Model: {response.model}")
        print(f"Created: {datetime.fromtimestamp(response.created)}")
        print("\nResponse Content:")
        print("-" * 80)
        print(response.choices[0].message.content)
        print("\nUsage Statistics:")
        print("-" * 80)
        print(f"Completion tokens: {response.usage.completion_tokens}")
        print(f"Prompt tokens: {response.usage.prompt_tokens}")
        print(f"Total tokens: {response.usage.total_tokens}")
        print("\nCitations:")
        print("-" * 80)
        for citation in response.citations:
            print(citation)
        print(f"\n{'='*80}\n")
