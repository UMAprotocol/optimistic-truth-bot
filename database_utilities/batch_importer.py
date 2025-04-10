#!/usr/bin/env python3
"""
Batch MongoDB Import Utility for UMA Oracle Results

This script imports multiple UMA oracle experiment results into MongoDB.
It can process the entire results directory or specific experiment directories.

Database Structure:
    - Experiment metadata is stored in the main collection (default: 'experiments')
    - Individual outputs are stored in a separate collection (default: '{collection_name}_outputs')
    - Each output document contains 'experiment_id' and 'question_id' for reference

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
import time
import argparse
import re
from pathlib import Path
from dotenv import load_dotenv
from pymongo import MongoClient, UpdateOne
from concurrent.futures import ThreadPoolExecutor
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("mongodb_import.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def setup_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Batch import UMA Oracle results into MongoDB"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--all",
        action="store_true",
        help="Process all experiments in results directory",
    )
    group.add_argument(
        "--experiments", nargs="+", help="Specific experiment directories to process"
    )
    parser.add_argument(
        "--results-dir",
        default="../proposal_replayer/results",
        help="Path to the results directory (default: ../proposal_replayer/results)",
    )
    parser.add_argument(
        "--database", default="uma_oracle", help="MongoDB database name"
    )
    parser.add_argument(
        "--collection", default="experiments", help="MongoDB collection name"
    )
    parser.add_argument(
        "--workers", type=int, default=4, help="Number of worker threads"
    )
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
        with open(metadata_path, "r") as f:
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
    if re.match(r"^[0-9a-f]{8}$", stem):
        return stem

    # Pattern 2: output_short_id
    output_match = re.match(r"^output_([0-9a-f]{8})$", stem)
    if output_match:
        return output_match.group(1)

    # Pattern 3: result_short_id_timestamp
    result_match = re.match(r"^result_([0-9a-f]{8})_", stem)
    if result_match:
        return result_match.group(1)

    # Return the stem as a fallback
    return stem


def load_output_files(outputs_dir):
    """Load all JSON output files from outputs directory."""
    output_files = {}

    for file_path in outputs_dir.glob("*.json"):
        try:
            # Skip metadata files
            if file_path.stem == "metadata":
                continue
                
            # Extract question_id using the same approach as output_watcher.py
            question_id = extract_question_id(file_path.name)
            
            # Extract timestamp if available
            timestamp_match = re.search(r'_(\d{8}_\d{6})', file_path.stem)
            timestamp = timestamp_match.group(1) if timestamp_match else "unknown"
            
            with open(file_path, "r") as f:
                data = json.load(f)
                # Sanitize data for MongoDB
                sanitize_for_mongodb(data)
                
                # Add metadata fields
                data["last_updated"] = timestamp
                data["last_updated_timestamp"] = int(time.time())
                data["source_file"] = str(file_path)
                
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
        # Get database
        db = client[database_name]

        # 1. Store experiment metadata in the main collection
        experiment_collection = db[collection_name]
        metadata_doc = {"experiment_id": experiment_id, "metadata": metadata}

        result = experiment_collection.update_one(
            {"experiment_id": experiment_id}, {"$set": metadata_doc}, upsert=True
        )

        if result.upserted_id:
            logger.info(
                f"Inserted experiment metadata {experiment_id} with ID {result.upserted_id}"
            )
        else:
            logger.info(f"Updated experiment metadata {experiment_id}")

        # 2. Store each output as a separate document in the outputs collection
        if outputs:
            outputs_collection = db[f"{collection_name}_outputs"]
            bulk_operations = []
            skipped_count = 0

            for question_id, output_data in outputs.items():
                # Add experiment_id reference to each output
                output_data["experiment_id"] = experiment_id
                output_data["question_id"] = question_id

                # Check if document already exists and if content is different
                existing_doc = outputs_collection.find_one(
                    {"experiment_id": experiment_id, "question_id": question_id}
                )
                
                if existing_doc:
                    # Create comparison copies without metadata fields
                    existing_copy = {k: v for k, v in existing_doc.items() 
                                   if k not in ["_id", "last_updated", "last_updated_timestamp", "source_file"]}
                    new_copy = {k: v for k, v in output_data.items() 
                               if k not in ["last_updated", "last_updated_timestamp", "source_file"]}
                    
                    # Only update if content has changed
                    if existing_copy != new_copy:
                        bulk_operations.append(
                            UpdateOne(
                                {"experiment_id": experiment_id, "question_id": question_id},
                                {"$set": output_data}
                            )
                        )
                    else:
                        skipped_count += 1
                else:
                    # Document doesn't exist, create insertion operation
                    bulk_operations.append(
                        UpdateOne(
                            {"experiment_id": experiment_id, "question_id": question_id},
                            {"$set": output_data},
                            upsert=True
                        )
                    )

            # Execute bulk operations in batches to prevent command size issues
            if bulk_operations:
                batch_size = 100
                for i in range(0, len(bulk_operations), batch_size):
                    batch = bulk_operations[i : i + batch_size]
                    if batch:
                        batch_result = outputs_collection.bulk_write(batch)
                        logger.info(
                            f"Batch {i//batch_size + 1}: Upserted {batch_result.upserted_count}, Modified {batch_result.modified_count} outputs"
                        )

                logger.info(
                    f"Processed {len(outputs)} outputs for experiment {experiment_id} (Skipped {skipped_count} unchanged documents)"
                )
            else:
                logger.info(
                    f"No updates needed for {len(outputs)} outputs in experiment {experiment_id} (all {skipped_count} documents unchanged)"
                )

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
        logger.error(
            f"Results directory {results_dir} does not exist or is not a directory"
        )
        return []

    experiment_dirs = []
    for item in results_path.iterdir():
        if (
            item.is_dir()
            and (item / "metadata.json").exists()
            and (item / "outputs").exists()
        ):
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
                logger.error(
                    f"No valid experiment directories found in {args.results_dir}"
                )
                client.close()
                sys.exit(1)

            logger.info(f"Found {len(experiment_dirs)} experiment directories")
        else:
            # Use specified experiment directories
            results_path = Path(args.results_dir)
            experiment_dirs = [results_path / exp for exp in args.experiments]

        # Process experiments in parallel
        with ThreadPoolExecutor(max_workers=args.workers) as executor:
            worker_args = [
                (str(exp_dir), args.database, args.collection, client)
                for exp_dir in experiment_dirs
            ]
            results = list(executor.map(import_worker, worker_args))

        # Report results
        success_count = sum(results)
        failure_count = len(results) - success_count

        logger.info(
            f"Import completed: {success_count} succeeded, {failure_count} failed"
        )

    finally:
        client.close()


if __name__ == "__main__":
    main()
