#!/usr/bin/env python3
"""
Test MongoDB connection and file processing for output_watcher.py
"""

import os
import json
import logging
from pathlib import Path
from dotenv import load_dotenv
from pymongo import MongoClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def get_mongo_client():
    """Get MongoDB client from MONGO_URI in .env file."""
    load_dotenv()
    mongo_uri = os.getenv("MONGO_URI")

    if not mongo_uri:
        logger.error("MONGO_URI not found in .env file")
        return None

    try:
        logger.info(f"Connecting to MongoDB with URI: {mongo_uri}")
        return MongoClient(mongo_uri)
    except Exception as e:
        logger.error(f"Error connecting to MongoDB: {e}")
        return None

def extract_question_id(file_name):
    """Extract the question_id from result file name."""
    import re
    stem = Path(file_name).stem
    
    # Pattern for result_short_id_timestamp
    result_match = re.match(r"^result_([0-9a-f]{8})_", stem)
    if result_match:
        return result_match.group(1)
    
    # Return the stem as a fallback
    logger.warning(f"Could not extract question_id from {file_name}")
    return stem

def sanitize_for_mongodb(data):
    """
    Sanitize data for MongoDB to handle known overflow issues.
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

def test_process_file(file_path, db_name="uma_oracle", collection_name="experiments"):
    """Test processing a single file."""
    try:
        # Convert to Path object
        file_path = Path(file_path)
        
        logger.info(f"Testing file processing for: {file_path}")
        
        # Check if file exists
        if not file_path.exists():
            logger.error(f"File does not exist: {file_path}")
            return False
            
        # Get experiment_id from directory structure
        experiment_dir = file_path.parent.parent
        experiment_id = experiment_dir.name
        logger.info(f"Experiment ID: {experiment_id}")
        
        # Get question_id from filename
        question_id = extract_question_id(file_path.name)
        logger.info(f"Question ID: {question_id}")
        
        # Load the JSON data
        with open(file_path, "r") as f:
            data = json.load(f)
            sanitize_for_mongodb(data)
        
        # Add experiment_id and question_id to the output data
        data["experiment_id"] = experiment_id
        data["question_id"] = question_id
        
        # Connect to MongoDB
        client = get_mongo_client()
        if client is None:
            return False
            
        try:
            # Access the database and collection
            db = client[db_name]
            outputs_collection = db[f"{collection_name}_outputs"]
            
            # Check for existing document
            existing = outputs_collection.find_one(
                {"experiment_id": experiment_id, "question_id": question_id}
            )
            
            if existing:
                logger.info(f"Found existing document for {question_id} in {experiment_id}")
            
            # Upsert the output document
            result = outputs_collection.update_one(
                {"experiment_id": experiment_id, "question_id": question_id},
                {"$set": data},
                upsert=True
            )
            
            if result.upserted_id:
                logger.info(f"Created new output document with ID: {result.upserted_id}")
            else:
                logger.info(f"Updated existing output document, modified count: {result.modified_count}")
                
            return True
            
        finally:
            client.close()
            
    except Exception as e:
        logger.error(f"Error processing file: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def test_directory_finding(watch_dir):
    """Test finding experiment directories."""
    watch_dir = Path(watch_dir)
    
    logger.info(f"Testing directory structure in: {watch_dir}")
    
    # Check if watch_dir exists
    if not watch_dir.exists():
        logger.error(f"Watch directory does not exist: {watch_dir}")
        return False
        
    # Check if it has metadata.json
    metadata_path = watch_dir / "metadata.json"
    if metadata_path.exists():
        logger.info(f"Found metadata.json: {metadata_path}")
    else:
        logger.warning(f"metadata.json not found in {watch_dir}")
        
    # Check if it has outputs directory
    outputs_dir = watch_dir / "outputs"
    if outputs_dir.exists() and outputs_dir.is_dir():
        logger.info(f"Found outputs directory: {outputs_dir}")
        # Count JSON files
        json_files = list(outputs_dir.glob("*.json"))
        logger.info(f"Found {len(json_files)} JSON files in outputs directory")
        for file in json_files:
            logger.info(f"  - {file.name}")
    else:
        logger.warning(f"outputs directory not found in {watch_dir}")
        
    return True

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python test_db_connection.py <test_type> [arguments]")
        print("Test types:")
        print("  connection - Test MongoDB connection")
        print("  directory <watch_dir> - Test directory structure detection")
        print("  process <file_path> - Test processing a specific file")
        sys.exit(1)
    
    test_type = sys.argv[1]
    
    if test_type == "connection":
        client = get_mongo_client()
        if client:
            logger.info("MongoDB connection successful!")
            client.close()
            
    elif test_type == "directory" and len(sys.argv) > 2:
        watch_dir = sys.argv[2]
        test_directory_finding(watch_dir)
        
    elif test_type == "process" and len(sys.argv) > 2:
        file_path = sys.argv[2]
        db_name = sys.argv[3] if len(sys.argv) > 3 else "uma_oracle"
        collection_name = sys.argv[4] if len(sys.argv) > 4 else "experiments"
        
        test_process_file(file_path, db_name, collection_name)
    else:
        logger.error(f"Unknown test type: {test_type}")