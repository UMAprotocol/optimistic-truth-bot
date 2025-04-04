#!/usr/bin/env python3
"""
MongoDB Import Utility for UMA Oracle Prompts

This script extracts prompt templates from various files in the UMA codebase
and imports them into MongoDB collections.

Usage:
    python prompts_to_mongodb.py [--database name]

Requirements:
    - Python 3.8+
    - pymongo
    - python-dotenv
"""

import os
import sys
import json
import argparse
import inspect
import importlib.util
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from pymongo import MongoClient


def setup_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Import UMA Oracle prompts into MongoDB"
    )
    parser.add_argument(
        "--database", default="uma_oracle", help="MongoDB database name"
    )
    return parser.parse_args()


def get_mongo_client():
    """Get MongoDB client from MONGO_URI in .env file."""
    load_dotenv()
    mongo_uri = os.getenv("MONGO_URI")

    if not mongo_uri:
        print("Error: MONGO_URI not found in .env file")
        sys.exit(1)

    try:
        return MongoClient(mongo_uri)
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")
        sys.exit(1)


def load_module_from_file(file_path):
    """Dynamically load a Python module from a file path."""
    try:
        module_name = Path(file_path).stem
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception as e:
        print(f"Error loading module from {file_path}: {e}")
        return None


def extract_main_prompts(module):
    """Extract prompt versions from the main prompt.py module."""
    prompts = []

    # Get the prompt versions dictionary
    prompt_versions = getattr(module, "PROMPT_VERSIONS", {})
    latest_version = getattr(module, "LATEST_VERSION", None)

    # Get current timestamp for example rendering
    current_time = int(datetime.now().timestamp())
    current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Process each prompt version
    for version, prompt_func in prompt_versions.items():
        try:
            # Get the raw template function
            prompt_template = inspect.getsource(prompt_func)

            # Generate an example rendered prompt
            example_prompt = prompt_func(current_time, current_datetime)

            prompts.append(
                {
                    "version": version,
                    "is_latest": version == latest_version,
                    "type": "main",
                    "template": prompt_template,
                    "example": example_prompt,
                    "updated_at": datetime.now(),
                }
            )
        except Exception as e:
            print(f"Error extracting prompt version {version}: {e}")

    return prompts


def extract_overseer_prompts(module):
    """Extract overseer prompts from the prompt_overseer.py module."""
    prompts = []

    # Get the overseer prompt function
    overseer_prompt_func = getattr(module, "get_overseer_prompt", None)
    base_system_prompt_func = getattr(module, "get_base_system_prompt", None)

    if overseer_prompt_func:
        try:
            # Get the raw template
            prompt_template = inspect.getsource(overseer_prompt_func)

            # Generate an example rendered prompt
            example_prompt = overseer_prompt_func(
                "Sample user prompt",
                "Sample system prompt",
                "Sample perplexity response",
                "p1",
                1,
            )

            prompts.append(
                {
                    "version": "v1",  # Default version since it's not versioned in the file
                    "is_latest": True,
                    "type": "overseer",
                    "template": prompt_template,
                    "example": example_prompt,
                    "updated_at": datetime.now(),
                }
            )
        except Exception as e:
            print(f"Error extracting overseer prompt: {e}")

    if base_system_prompt_func:
        try:
            # Get the raw template
            prompt_template = inspect.getsource(base_system_prompt_func)

            # Get the example prompt
            example_prompt = base_system_prompt_func()

            prompts.append(
                {
                    "version": "v1",  # Default version since it's not versioned in the file
                    "is_latest": True,
                    "type": "overseer_base",
                    "template": prompt_template,
                    "example": example_prompt,
                    "updated_at": datetime.now(),
                }
            )
        except Exception as e:
            print(f"Error extracting base system prompt: {e}")

    # Extract format_market_price_info if it exists
    market_info_format_func = getattr(module, "format_market_price_info", None)
    if market_info_format_func:
        try:
            # Get the raw template
            prompt_template = inspect.getsource(market_info_format_func)

            # Get an example (with dummy tokens)
            example_tokens = [
                {"outcome": "YES", "price": 0.75, "token_id": "123", "winner": False},
                {"outcome": "NO", "price": 0.25, "token_id": "456", "winner": False},
            ]
            example_prompt = market_info_format_func(example_tokens)

            prompts.append(
                {
                    "version": "v1",
                    "is_latest": True,
                    "type": "market_price_formatter",
                    "template": prompt_template,
                    "example": example_prompt,
                    "updated_at": datetime.now(),
                }
            )
        except Exception as e:
            print(f"Error extracting market price formatter: {e}")

    return prompts


def extract_router_prompts(module):
    """Extract router prompts from the router.py module."""
    prompts = []

    # Get the router prompt function
    router_prompt_func = getattr(module, "Router", None)

    if router_prompt_func:
        try:
            # Create a temporary instance to access the method
            router_instance = router_prompt_func("dummy_api_key")
            get_router_prompt_func = getattr(router_instance, "get_router_prompt", None)

            if get_router_prompt_func:
                # Get the raw template
                prompt_template = inspect.getsource(get_router_prompt_func)

                # Generate an example rendered prompt
                example_prompt = get_router_prompt_func(
                    "What was the price of Bitcoin on March 1st, 2023?",
                    ["perplexity", "code_runner"],
                )

                prompts.append(
                    {
                        "version": "v1",  # Default version
                        "is_latest": True,
                        "type": "router",
                        "template": prompt_template,
                        "example": example_prompt,
                        "updated_at": datetime.now(),
                    }
                )
        except Exception as e:
            print(f"Error extracting router prompt: {e}")

    return prompts


def extract_code_runner_prompts(module):
    """Extract code runner prompts from the code_runner_solver.py module."""
    prompts = []

    # Get the CodeRunnerSolver class
    solver_class = getattr(module, "CodeRunnerSolver", None)

    if solver_class:
        try:
            # Create a temporary instance to access the methods
            solver_instance = solver_class("dummy_api_key")

            # Extract code generation prompt
            generate_code_func = getattr(solver_instance, "generate_code", None)
            if generate_code_func:
                # Get the raw template
                prompt_template = inspect.getsource(generate_code_func)

                prompts.append(
                    {
                        "version": "v1",
                        "is_latest": True,
                        "type": "code_runner_generate",
                        "template": prompt_template,
                        "example": "See template for code generation logic",
                        "updated_at": datetime.now(),
                    }
                )

            # Extract code feedback prompt
            generate_feedback_func = getattr(
                solver_instance, "generate_code_with_output_feedback", None
            )
            if generate_feedback_func:
                # Get the raw template
                prompt_template = inspect.getsource(generate_feedback_func)

                prompts.append(
                    {
                        "version": "v1",
                        "is_latest": True,
                        "type": "code_runner_feedback",
                        "template": prompt_template,
                        "example": "See template for code feedback logic",
                        "updated_at": datetime.now(),
                    }
                )

            # Extract query type determination prompt
            determine_query_type_func = getattr(
                solver_instance, "determine_query_type", None
            )
            if determine_query_type_func:
                # Get the raw template
                prompt_template = inspect.getsource(determine_query_type_func)

                prompts.append(
                    {
                        "version": "v1",
                        "is_latest": True,
                        "type": "code_runner_query_type",
                        "template": prompt_template,
                        "example": "See template for query type determination logic",
                        "updated_at": datetime.now(),
                    }
                )

            # Extract output processing prompt
            process_output_func = getattr(solver_instance, "process_code_output", None)
            if process_output_func:
                # Get the raw template
                prompt_template = inspect.getsource(process_output_func)

                prompts.append(
                    {
                        "version": "v1",
                        "is_latest": True,
                        "type": "code_runner_process_output",
                        "template": prompt_template,
                        "example": "See template for output processing logic",
                        "updated_at": datetime.now(),
                    }
                )
        except Exception as e:
            print(f"Error extracting code runner prompts: {e}")

    return prompts


def import_prompts_to_mongodb(client, database_name, prompts):
    """Import prompts into MongoDB."""
    db = client[database_name]
    collection = db["prompts"]

    # Import each prompt with upsert logic
    for prompt in prompts:
        # The unique identifiers for a prompt are type and version
        result = collection.update_one(
            {"type": prompt["type"], "version": prompt["version"]},
            {"$set": prompt},
            upsert=True,
        )

        if result.upserted_id:
            print(
                f"Inserted {prompt['type']} prompt version {prompt['version']} with ID {result.upserted_id}"
            )
        else:
            print(
                f"Updated {prompt['type']} prompt version {prompt['version']}, modified {result.modified_count} document(s)"
            )

    return True


def main():
    """Main entry point for the script."""
    args = setup_arguments()

    # Connect to MongoDB
    client = get_mongo_client()

    # Path to the prompt files
    project_root = Path(__file__).parent.parent
    main_prompt_path = project_root / "prompt.py"
    overseer_prompt_path = project_root / "proposal_overseer" / "prompt_overseer.py"
    router_prompt_path = project_root / "multi_operator" / "router" / "router.py"
    code_runner_prompt_path = (
        project_root
        / "multi_operator"
        / "solvers"
        / "code_runner"
        / "code_runner_solver.py"
    )

    # Verify necessary files exist
    all_prompts = []

    # Load and extract main prompts if file exists
    if main_prompt_path.exists():
        main_prompt_module = load_module_from_file(main_prompt_path)
        if main_prompt_module:
            main_prompts = extract_main_prompts(main_prompt_module)
            all_prompts.extend(main_prompts)
            print(f"Extracted {len(main_prompts)} main prompts")
    else:
        print(f"Warning: Main prompt file not found at {main_prompt_path}")

    # Load and extract overseer prompts if file exists
    if overseer_prompt_path.exists():
        overseer_prompt_module = load_module_from_file(overseer_prompt_path)
        if overseer_prompt_module:
            overseer_prompts = extract_overseer_prompts(overseer_prompt_module)
            all_prompts.extend(overseer_prompts)
            print(f"Extracted {len(overseer_prompts)} overseer prompts")
    else:
        print(f"Warning: Overseer prompt file not found at {overseer_prompt_path}")

    # Try the multi_operator overseer path if the original one is not found
    if not overseer_prompt_path.exists():
        alt_overseer_path = (
            project_root / "multi_operator" / "overseer" / "prompt_overseer.py"
        )
        if alt_overseer_path.exists():
            overseer_prompt_module = load_module_from_file(alt_overseer_path)
            if overseer_prompt_module:
                overseer_prompts = extract_overseer_prompts(overseer_prompt_module)
                all_prompts.extend(overseer_prompts)
                print(
                    f"Extracted {len(overseer_prompts)} overseer prompts from alternate location"
                )

    # Load and extract router prompts if file exists
    if router_prompt_path.exists():
        router_prompt_module = load_module_from_file(router_prompt_path)
        if router_prompt_module:
            router_prompts = extract_router_prompts(router_prompt_module)
            all_prompts.extend(router_prompts)
            print(f"Extracted {len(router_prompts)} router prompts")
    else:
        print(f"Warning: Router prompt file not found at {router_prompt_path}")

    # Load and extract code runner prompts if file exists
    if code_runner_prompt_path.exists():
        code_runner_module = load_module_from_file(code_runner_prompt_path)
        if code_runner_module:
            code_runner_prompts = extract_code_runner_prompts(code_runner_module)
            all_prompts.extend(code_runner_prompts)
            print(f"Extracted {len(code_runner_prompts)} code runner prompts")
    else:
        print(
            f"Warning: Code runner prompt file not found at {code_runner_prompt_path}"
        )

    # Import prompts to MongoDB
    if all_prompts:
        success = import_prompts_to_mongodb(client, args.database, all_prompts)

        if success:
            print(f"Successfully imported {len(all_prompts)} prompts to MongoDB")
        else:
            print("Error importing prompts to MongoDB")
            client.close()
            sys.exit(1)
    else:
        print("No prompts were extracted. Check file paths and module structures.")
        client.close()
        sys.exit(1)

    # Close MongoDB connection
    client.close()


if __name__ == "__main__":
    main()
