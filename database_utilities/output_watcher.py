#!/usr/bin/env python3
"""
MongoDB Output Watcher for UMA Oracle

This script watches the results directory for new files and automatically
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
import re
from pathlib import Path
from dotenv import load_dotenv
from pymongo import MongoClient
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent

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
    parser.add_argument('--watch-dir', default='../results', 
                      help='Directory containing experiment results to watch')
    parser.add_argument('--database', default='uma_oracle', help='MongoDB database name')
    parser.add_argument('--collection', default='experiments', help='MongoDB collection name')
    parser.add_argument('--refresh-interval', type=int, default=60, 
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

def extract_question_id(file_name):
    """
    Extract the question_id from various file naming patterns.
    Supports formats like:
    - short_id.json (e.g., 025eb1be.json)
    - output_short_id.json (e.g., output_05c5a914.json)
    - result_short_id_timestamp.json (e.g., result_e5373cc5_20250402_102821.json)
    """
    stem = Path(file_name).stem
    
    # Pattern 1: short_id
    if re.match(r'^[0-9a-f]{8}$', stem):
        return stem
    
    # Pattern 2: output_short_id
    output_match = re.match(r'^output_([0-9a-f]{8})$', stem)
    if output_match:
        return output_match.group(1)
    
    # Pattern 3: result_short_id_timestamp
    result_match = re.match(r'^result_([0-9a-f]{8})_', stem)
    if result_match:
        return result_match.group(1)
    
    # Return the stem as a fallback
    return stem

def process_output_file(file_path, db, collection_name):
    """Process a single output file and add it to MongoDB."""
    try:
        # Get experiment_id from directory structure
        experiment_dir = file_path.parent.parent
        experiment_id = experiment_dir.name
        
        # Get question_id from filename
        file_stem = file_path.stem
        
        # Skip metadata.json files
        if file_stem == 'metadata':
            return False
        
        # Extract question_id from the filename
        question_id = extract_question_id(file_path.name)
        
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

class ExperimentObserver:
    """Manages watching experiment directories for changes."""
    
    def __init__(self, watch_dir, db, collection_name, refresh_interval=60):
        self.watch_dir = Path(watch_dir)
        self.db = db
        self.collection_name = collection_name
        self.refresh_interval = refresh_interval
        self.observer = Observer()
        self.handler = OutputFileHandler(db, collection_name)
        self.watched_experiments = set()
    
    def find_experiments(self):
        """Find all experiment directories in the watch directory."""
        if not self.watch_dir.exists():
            logger.error(f"Watch directory {self.watch_dir} does not exist")
            return []
        
        experiments = []
        try:
            for item in self.watch_dir.iterdir():
                if item.is_dir() and (item / "metadata.json").exists() and (item / "outputs").exists():
                    experiments.append(item)
        except Exception as e:
            logger.error(f"Error scanning for experiments: {e}")
        
        return experiments
    
    def find_output_files(self, experiment_dir):
        """Find all output files in an experiment directory."""
        outputs_dir = experiment_dir / "outputs"
        return list(outputs_dir.glob("*.json"))
    
    def start_watching(self):
        """Start watching for file system events."""
        # Start the observer
        self.observer.start()
        logger.info("File system observer started")
        
        try:
            while True:
                # Check for new experiment directories periodically
                self.check_for_new_experiments()
                time.sleep(self.refresh_interval)
                
        except KeyboardInterrupt:
            logger.info("Stopping observer due to keyboard interrupt")
            self.observer.stop()
        except Exception as e:
            logger.error(f"Error in observer loop: {e}")
            self.observer.stop()
        
        self.observer.join()
    
    def check_for_new_experiments(self):
        """Check for new experiment directories and start watching them."""
        current_experiments = self.find_experiments()
        
        for experiment in current_experiments:
            exp_str = str(experiment)
            if exp_str not in self.watched_experiments:
                outputs_dir = experiment / "outputs"
                
                # Schedule watching this directory
                try:
                    if outputs_dir.exists():
                        self.observer.schedule(self.handler, str(outputs_dir), recursive=False)
                        logger.info(f"New experiment detected, watching directory: {outputs_dir}")
                        
                        # Process existing files in the directory
                        for file_path in self.find_output_files(experiment):
                            # Create a synthetic event to process the file
                            event = FileCreatedEvent(str(file_path))
                            self.handler.on_created(event)
                        
                        self.watched_experiments.add(exp_str)
                    else:
                        logger.warning(f"Outputs directory not found for experiment: {experiment}")
                except Exception as e:
                    logger.error(f"Error scheduling observer for {outputs_dir}: {e}")

def initial_import(watch_dir, db, collection_name):
    """Import all existing output files on startup."""
    logger.info("Performing initial import of existing files...")
    
    observer = ExperimentObserver(watch_dir, db, collection_name)
    experiments = observer.find_experiments()
    logger.info(f"Found {len(experiments)} experiment directories")
    
    total_files = 0
    imported_files = 0
    
    for experiment in experiments:
        output_files = observer.find_output_files(experiment)
        total_files += len(output_files)
        
        for file_path in output_files:
            success = process_output_file(file_path, db, collection_name)
            if success:
                imported_files += 1
    
    logger.info(f"Initial import complete: {imported_files}/{total_files} files imported")

def main():
    """Main entry point for the script."""
    args = setup_arguments()
    
    # Resolve watch directory to absolute path
    watch_dir = os.path.abspath(args.watch_dir)
    logger.info(f"Watching directory: {watch_dir}")
    
    # Connect to MongoDB
    client = get_mongo_client()
    if client is None:
        sys.exit(1)
    
    db = client[args.database]
    
    try:
        # Perform initial import of existing files
        initial_import(watch_dir, db, args.collection)
        
        # Start watching for new files
        experiment_observer = ExperimentObserver(
            watch_dir, db, args.collection, args.refresh_interval
        )
        experiment_observer.start_watching()
    
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    main()