#!/usr/bin/env python3
"""
MongoDB Output Watcher for UMA Oracle

This script watches the outputs directory for new files and automatically
imports them into MongoDB. It's designed to run as a daemon process.

Usage:
    python output_watcher.py [--watch-dir path] [--database name] [--collection name]

Requirements:
    - Python 3.8+
    - pymongo
    - python-dotenv
    - watchdog
"""

import os
import sys
import time
import json
import logging
import argparse
from pathlib import Path
from dotenv import load_dotenv
from pymongo import MongoClient
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("output_watcher.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def setup_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Watch output files and import to MongoDB')
    parser.add_argument('--watch-dir', default='../proposal_replayer/results', 
                      help='Directory containing experiment results to watch')
    parser.add_argument('--database', default='uma_oracle', help='MongoDB database name')
    parser.add_argument('--collection', default='experiments', help='MongoDB collection name')
    parser.add_argument('--refresh-interval', type=int, default=10, 
                      help='Directory scan refresh interval in seconds')
    return parser.parse_args()

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

def process_output_file(file_path, db, collection_name):
    """Process a single output file and add it to MongoDB."""
    try:
        # Get experiment_id from directory structure
        experiment_dir = file_path.parent.parent
        experiment_id = experiment_dir.name
        question_id = file_path.stem
        
        # Check if this is a valid output file (not metadata or some other file)
        if not question_id or question_id.startswith('.') or question_id == 'metadata':
            return False
        
        # Load the JSON data
        with open(file_path, 'r') as f:
            data = json.load(f)
            sanitize_for_mongodb(data)
        
        # Get the collection
        collection = db[collection_name]
        
        # Update the experiment document with this output
        result = collection.update_one(
            {"experiment_id": experiment_id},
            {"$set": {f"outputs.{question_id}": data}},
            upsert=True
        )
        
        if result.upserted_id:
            logger.info(f"Created new experiment {experiment_id} with output {question_id}")
        else:
            logger.info(f"Updated experiment {experiment_id} with output {question_id}")
        
        return True
    
    except json.JSONDecodeError:
        logger.warning(f"Invalid JSON in {file_path}, skipping file")
        return False
    except Exception as e:
        logger.error(f"Error processing file {file_path}: {e}")
        return False

class OutputFileHandler(FileSystemEventHandler):
    """Handler for file system events in the watched directory."""
    
    def __init__(self, db, collection_name):
        self.db = db
        self.collection_name = collection_name
        super().__init__()
    
    def on_created(self, event):
        """Handle file creation events."""
        if not event.is_directory and event.src_path.endswith('.json'):
            file_path = Path(event.src_path)
            logger.info(f"New file detected: {file_path}")
            process_output_file(file_path, self.db, self.collection_name)
    
    def on_modified(self, event):
        """Handle file modification events."""
        if not event.is_directory and event.src_path.endswith('.json'):
            file_path = Path(event.src_path)
            logger.info(f"Modified file detected: {file_path}")
            process_output_file(file_path, self.db, self.collection_name)

def find_experiments(watch_dir):
    """Find all experiment directories in the watch directory."""
    watch_path = Path(watch_dir)
    if not watch_path.exists():
        logger.error(f"Watch directory {watch_dir} does not exist")
        return []
    
    experiments = []
    for item in watch_path.iterdir():
        if item.is_dir() and (item / "metadata.json").exists() and (item / "outputs").exists():
            experiments.append(item)
    
    return experiments

def find_output_files(experiment_dir):
    """Find all output files in an experiment directory."""
    outputs_dir = experiment_dir / "outputs"
    return list(outputs_dir.glob("*.json"))

def initial_import(watch_dir, db, collection_name):
    """Import all existing output files on startup."""
    logger.info("Performing initial import of existing files...")
    
    experiments = find_experiments(watch_dir)
    logger.info(f"Found {len(experiments)} experiment directories")
    
    total_files = 0
    imported_files = 0
    
    for experiment in experiments:
        output_files = find_output_files(experiment)
        total_files += len(output_files)
        
        for file_path in output_files:
            success = process_output_file(file_path, db, collection_name)
            if success:
                imported_files += 1
    
    logger.info(f"Initial import complete: {imported_files}/{total_files} files imported")

def start_watching(watch_dir, db, collection_name):
    """Start watching for file system events."""
    event_handler = OutputFileHandler(db, collection_name)
    observer = Observer()
    
    # Watch all experiment directories
    experiments = find_experiments(watch_dir)
    for experiment in experiments:
        outputs_dir = experiment / "outputs"
        observer.schedule(event_handler, str(outputs_dir), recursive=False)
        logger.info(f"Watching directory: {outputs_dir}")
    
    # Start the observer
    observer.start()
    logger.info("File system observer started")
    
    try:
        while True:
            # Check for new experiment directories periodically
            time.sleep(60)
            
            current_experiments = find_experiments(watch_dir)
            new_experiments = [exp for exp in current_experiments if exp not in experiments]
            
            for experiment in new_experiments:
                outputs_dir = experiment / "outputs"
                observer.schedule(event_handler, str(outputs_dir), recursive=False)
                logger.info(f"New experiment detected, watching directory: {outputs_dir}")
            
            experiments = current_experiments
            
    except KeyboardInterrupt:
        observer.stop()
    
    observer.join()

def main():
    """Main entry point for the script."""
    args = setup_arguments()
    
    # Connect to MongoDB
    client = get_mongo_client()
    if client is None:
        sys.exit(1)
    
    db = client[args.database]
    
    try:
        # Perform initial import of existing files
        initial_import(args.watch_dir, db, args.collection)
        
        # Start watching for new files
        start_watching(args.watch_dir, db, args.collection)
    
    finally:
        client.close()

if __name__ == "__main__":
    main()