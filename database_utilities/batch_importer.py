#!/usr/bin/env python3
"""
Batch MongoDB Import Utility for UMA Oracle Results

This script imports multiple UMA oracle experiment results into MongoDB.
It can process the entire results directory or specific experiment directories.

Usage:
    python batch_importer.py --all  # Process all experiments in results directory
    python batch_importer.py --experiments exp1 exp2  # Process specific experiment directories

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
from concurrent.futures import ThreadPoolExecutor
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("mongodb_import.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def setup_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Batch import UMA Oracle results into MongoDB')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--all', action='store_true', help='Process all experiments in results directory')
    group.add_argument('--experiments', nargs='+', help='Specific experiment directories to process')
    parser.add_argument('--results-dir', default='../proposal_replayer/results', 
                      help='Path to the results directory (default: ../proposal_replayer/results)')
    parser.add_argument('--database', default='uma_oracle', help='MongoDB database name')
    parser.add_argument('--collection', default='experiments', help='MongoDB collection name')
    parser.add_argument('--workers', type=int, default=4, help='Number of worker threads')
    return parser.parse_args()

def validate_experiment_dir(experiment_dir):
    """Validate that the experiment directory has the required structure."""
    exp_path = Path(experiment_dir)
    
    if not exp_path.exists():
        logger.error(f"Directory {experiment_dir} does not exist.")
        return None, None, None
        
    metadata_path = exp_path / "metadata.json"
    outputs_dir = exp_path / "outputs"
    
    if not metadata_path.exists():
        logger.error(f"metadata.json not found in {experiment_dir}")
        return None, None, None
        
    if not outputs_dir.exists() or not outputs_dir.is_dir():
        logger.error(f"outputs/ directory not found in {experiment_dir}")
        return None, None, None
        
    return exp_path, metadata_path, outputs_dir

def load_metadata(metadata_path):
    """Load experiment metadata from metadata.json."""
    try:
        with open(metadata_path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in {metadata_path}")
        return None
    except Exception as e:
        logger.error(f"Error reading metadata file: {e}")
        return None

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
            logger.warning(f"Invalid JSON in {file_path}, skipping file")
            continue
        except Exception as e:
            logger.warning(f"Error reading file {file_path}: {e}, skipping file")
            continue
            
    return output_files

def get_mongo_client():
    """Get MongoDB client from MONGO_URI in .env file."""
    load_dotenv()
    mongo_uri = os.getenv("MONGO_URI")
    
    if not mongo_uri:
        logger.error("MONGO_URI not found in .env file")
        return None
        
    try:
        return MongoClient(mongo_uri)
    except Exception as e:
        logger.error(f"Error connecting to MongoDB: {e}")
        return None

def import_experiment(experiment_dir, database_name, collection_name, client=None):
    """Import single experiment data into MongoDB."""
    should_close = False
    if client is None:
        client = get_mongo_client()
        should_close = True
        if client is None:
            return False
    
    # Validate experiment directory
    exp_path, metadata_path, outputs_dir = validate_experiment_dir(experiment_dir)
    if exp_path is None:
        return False
    
    # Load metadata and output files
    metadata = load_metadata(metadata_path)
    if metadata is None:
        return False
        
    outputs = load_output_files(outputs_dir)
    if not outputs:
        logger.warning(f"No valid output files found in {outputs_dir}")
    
    logger.info(f"Loaded metadata and {len(outputs)} output files from {exp_path}")
    
    # Extract experiment ID from directory name
    experiment_id = exp_path.name
    
    try:
        # Get database and collection
        db = client[database_name]
        collection = db[collection_name]
        
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
            logger.info(f"Inserted experiment {experiment_id} with ID {result.upserted_id}")
        else:
            logger.info(f"Updated experiment {experiment_id}, modified {result.modified_count} document(s)")
        
        if should_close:
            client.close()
            
        return True
    
    except Exception as e:
        logger.error(f"Error importing experiment {experiment_id}: {e}")
        if should_close and client:
            client.close()
        return False

def discover_experiments(results_dir):
    """Discover all experiment directories in the results directory."""
    results_path = Path(results_dir)
    if not results_path.exists() or not results_path.is_dir():
        logger.error(f"Results directory {results_dir} does not exist or is not a directory")
        return []
    
    experiment_dirs = []
    for item in results_path.iterdir():
        if item.is_dir() and (item / "metadata.json").exists() and (item / "outputs").exists():
            experiment_dirs.append(item)
    
    return experiment_dirs

def import_worker(args):
    """Worker function for thread pool."""
    experiment_dir, database_name, collection_name, client = args
    return import_experiment(experiment_dir, database_name, collection_name, client)

def main():
    """Main entry point for the script."""
    args = setup_arguments()
    
    # Connect to MongoDB once
    client = get_mongo_client()
    if client is None:
        sys.exit(1)
    
    try:
        if args.all:
            # Discover all experiment directories
            experiment_dirs = discover_experiments(args.results_dir)
            if not experiment_dirs:
                logger.error(f"No valid experiment directories found in {args.results_dir}")
                client.close()
                sys.exit(1)
            
            logger.info(f"Found {len(experiment_dirs)} experiment directories")
        else:
            # Use specified experiment directories
            results_path = Path(args.results_dir)
            experiment_dirs = [results_path / exp for exp in args.experiments]
        
        # Process experiments in parallel
        with ThreadPoolExecutor(max_workers=args.workers) as executor:
            worker_args = [(str(exp_dir), args.database, args.collection, client) for exp_dir in experiment_dirs]
            results = list(executor.map(import_worker, worker_args))
        
        # Report results
        success_count = sum(results)
        failure_count = len(results) - success_count
        
        logger.info(f"Import completed: {success_count} succeeded, {failure_count} failed")
        
    finally:
        client.close()

if __name__ == "__main__":
    main()