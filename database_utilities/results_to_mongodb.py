#!/usr/bin/env python3
"""
MongoDB Import Utility for UMA Oracle Results

This script imports UMA oracle experiment results into MongoDB.
It takes a directory containing metadata.json and outputs/ subdirectory
and imports all data into a MongoDB collection, preserving the structure.

Usage:
    python results_to_mongodb.py /path/to/experiment/directory [--database name] [--collection name]

Requirements:
    - Python 3.8+
    - pymongo
    - python-dotenv
"""

import os
import sys
import json
import argparse
from pathlib import Path
from dotenv import load_dotenv
from pymongo import MongoClient, UpdateOne

def setup_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Import UMA Oracle results into MongoDB')
    parser.add_argument('experiment_dir', help='Directory containing metadata.json and outputs/')
    parser.add_argument('--database', default='uma_oracle', help='MongoDB database name')
    parser.add_argument('--collection', default='experiments', help='MongoDB collection name')
    return parser.parse_args()

def validate_experiment_dir(experiment_dir):
    """Validate that the experiment directory has the required structure."""
    exp_path = Path(experiment_dir)
    
    if not exp_path.exists():
        print(f"Error: Directory {experiment_dir} does not exist.")
        sys.exit(1)
        
    metadata_path = exp_path / "metadata.json"
    outputs_dir = exp_path / "outputs"
    
    if not metadata_path.exists():
        print(f"Error: metadata.json not found in {experiment_dir}")
        sys.exit(1)
        
    if not outputs_dir.exists() or not outputs_dir.is_dir():
        print(f"Error: outputs/ directory not found in {experiment_dir}")
        sys.exit(1)
        
    return exp_path, metadata_path, outputs_dir

def load_metadata(metadata_path):
    """Load experiment metadata from metadata.json."""
    try:
        with open(metadata_path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in {metadata_path}")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading metadata file: {e}")
        sys.exit(1)

def sanitize_for_mongodb(data):
    """
    Sanitize data for MongoDB to handle known overflow issues.
    Converts only the specific large integers that would cause MongoDB overflow.
    """
    if isinstance(data, dict):
        for key, value in list(data.items()):
            # Convert known large integer fields to strings
            if key in ["proposed_price", "resolved_price"] and isinstance(value, int):
                data[key] = str(value)
            elif isinstance(value, (dict, list)):
                sanitize_for_mongodb(value)
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, (dict, list)):
                sanitize_for_mongodb(item)
    return data

def load_output_files(outputs_dir):
    """Load all JSON output files from outputs directory."""
    output_files = {}
    
    for file_path in outputs_dir.glob("*.json"):
        try:
            with open(file_path, 'r') as f:
                question_id = file_path.stem
                data = json.load(f)
                # Sanitize data for MongoDB
                sanitize_for_mongodb(data)
                output_files[question_id] = data
        except json.JSONDecodeError:
            print(f"Warning: Invalid JSON in {file_path}, skipping file")
            continue
        except Exception as e:
            print(f"Warning: Error reading file {file_path}: {e}, skipping file")
            continue
            
    return output_files

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

def import_to_mongodb(client, database_name, collection_name, experiment_dir, metadata, outputs):
    """Import experiment data into MongoDB."""
    db = client[database_name]
    collection = db[collection_name]
    
    # Extract experiment ID from directory name
    experiment_id = experiment_dir.name
    
    # Create document structure
    experiment_doc = {
        "experiment_id": experiment_id,
        "metadata": metadata,
        "outputs": outputs
    }
    
    # Upsert the document (update if exists, insert if not)
    result = collection.update_one(
        {"experiment_id": experiment_id},
        {"$set": experiment_doc},
        upsert=True
    )
    
    if result.upserted_id:
        print(f"Inserted experiment {experiment_id} with ID {result.upserted_id}")
    else:
        print(f"Updated experiment {experiment_id}, modified {result.modified_count} document(s)")
    
    return result

def main():
    """Main entry point for the script."""
    args = setup_arguments()
    
    # Validate experiment directory
    exp_path, metadata_path, outputs_dir = validate_experiment_dir(args.experiment_dir)
    
    # Load metadata and output files
    metadata = load_metadata(metadata_path)
    outputs = load_output_files(outputs_dir)
    
    print(f"Loaded metadata and {len(outputs)} output files from {exp_path}")
    
    # Connect to MongoDB
    client = get_mongo_client()
    
    # Import data
    result = import_to_mongodb(
        client, 
        args.database, 
        args.collection, 
        exp_path, 
        metadata, 
        outputs
    )
    
    client.close()
    print("Import completed successfully")

if __name__ == "__main__":
    main()