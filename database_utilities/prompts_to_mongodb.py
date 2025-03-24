#!/usr/bin/env python3
"""
MongoDB Import Utility for UMA Oracle Prompts

This script extracts prompt templates from prompt.py and prompt_overseer.py
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
    parser = argparse.ArgumentParser(description='Import UMA Oracle prompts into MongoDB')
    parser.add_argument('--database', default='uma_oracle', help='MongoDB database name')
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
    prompt_versions = getattr(module, 'PROMPT_VERSIONS', {})
    latest_version = getattr(module, 'LATEST_VERSION', None)
    
    # Get current timestamp for example rendering
    current_time = int(datetime.now().timestamp())
    current_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Process each prompt version
    for version, prompt_func in prompt_versions.items():
        try:
            # Get the raw template function
            prompt_template = inspect.getsource(prompt_func)
            
            # Generate an example rendered prompt
            example_prompt = prompt_func(current_time, current_datetime)
            
            prompts.append({
                'version': version,
                'is_latest': version == latest_version,
                'type': 'main',
                'template': prompt_template,
                'example': example_prompt,
                'updated_at': datetime.now()
            })
        except Exception as e:
            print(f"Error extracting prompt version {version}: {e}")
    
    return prompts

def extract_overseer_prompts(module):
    """Extract overseer prompts from the prompt_overseer.py module."""
    prompts = []
    
    # Get the overseer prompt function
    overseer_prompt_func = getattr(module, 'get_overseer_prompt', None)
    base_system_prompt_func = getattr(module, 'get_base_system_prompt', None)
    
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
                1
            )
            
            prompts.append({
                'version': 'v1',  # Default version since it's not versioned in the file
                'is_latest': True,
                'type': 'overseer',
                'template': prompt_template,
                'example': example_prompt,
                'updated_at': datetime.now()
            })
        except Exception as e:
            print(f"Error extracting overseer prompt: {e}")
    
    if base_system_prompt_func:
        try:
            # Get the raw template
            prompt_template = inspect.getsource(base_system_prompt_func)
            
            # Get the example prompt
            example_prompt = base_system_prompt_func()
            
            prompts.append({
                'version': 'v1',  # Default version since it's not versioned in the file
                'is_latest': True,
                'type': 'overseer_base',
                'template': prompt_template,
                'example': example_prompt,
                'updated_at': datetime.now()
            })
        except Exception as e:
            print(f"Error extracting base system prompt: {e}")
    
    return prompts

def import_prompts_to_mongodb(client, database_name, prompts):
    """Import prompts into MongoDB."""
    db = client[database_name]
    collection = db['prompts']
    
    # Import each prompt with upsert logic
    for prompt in prompts:
        # The unique identifiers for a prompt are type and version
        result = collection.update_one(
            {
                'type': prompt['type'],
                'version': prompt['version']
            },
            {'$set': prompt},
            upsert=True
        )
        
        if result.upserted_id:
            print(f"Inserted {prompt['type']} prompt version {prompt['version']} with ID {result.upserted_id}")
        else:
            print(f"Updated {prompt['type']} prompt version {prompt['version']}, modified {result.modified_count} document(s)")
    
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
    
    # Verify files exist
    if not main_prompt_path.exists():
        print(f"Error: Main prompt file not found at {main_prompt_path}")
        client.close()
        sys.exit(1)
    
    if not overseer_prompt_path.exists():
        print(f"Error: Overseer prompt file not found at {overseer_prompt_path}")
        client.close()
        sys.exit(1)
    
    # Load the modules
    main_prompt_module = load_module_from_file(main_prompt_path)
    overseer_prompt_module = load_module_from_file(overseer_prompt_path)
    
    if not main_prompt_module or not overseer_prompt_module:
        client.close()
        sys.exit(1)
    
    # Extract prompts
    main_prompts = extract_main_prompts(main_prompt_module)
    overseer_prompts = extract_overseer_prompts(overseer_prompt_module)
    
    # Combine all prompts
    all_prompts = main_prompts + overseer_prompts
    
    # Import prompts to MongoDB
    success = import_prompts_to_mongodb(client, args.database, all_prompts)
    
    # Close MongoDB connection
    client.close()
    
    if success:
        print(f"Successfully imported {len(all_prompts)} prompts to MongoDB")
    else:
        print("Error importing prompts to MongoDB")
        sys.exit(1)

if __name__ == "__main__":
    main()