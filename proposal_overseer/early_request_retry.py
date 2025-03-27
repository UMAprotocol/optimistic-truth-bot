#!/usr/bin/env python3
"""
UMA Early Request Retry - Monitors directories for P4 recommendations that have not expired and retries them.
Usage: python proposal_overseer/early_request_retry.py [--output-dir PATH] [--check-interval SECONDS]
"""

import os
import json
import time
import sys
import argparse
from pathlib import Path
import datetime
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from dotenv import load_dotenv

# Add the parent directory to the path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from prompt import get_system_prompt

# Import locally defined modules
from proposal_overseer.common import (
    setup_logging,
    extract_recommendation,
    query_perplexity,
    query_chatgpt,
    enhanced_perplexity_chatgpt_loop,
)

# Parse command line arguments
parser = argparse.ArgumentParser(
    description="UMA Early Request Retry - Monitor for P4 recommendations that haven't expired"
)

parser.add_argument(
    "--output-dir", type=str, help="Directory to store output files"
)

parser.add_argument(
    "--check-interval", 
    type=int, 
    default=300, 
    help="Time in seconds between checks for expired requests (default: 300)"
)

args = parser.parse_args()

# Setup logging
logger = setup_logging("early_request_retry", "logs/early_request_retry.log")
load_dotenv()
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Verify API keys are available
if not PERPLEXITY_API_KEY:
    logger.error("PERPLEXITY_API_KEY not found in environment variables")
    sys.exit(1)

if not OPENAI_API_KEY:
    logger.error("OPENAI_API_KEY not found in environment variables")
    sys.exit(1)

# Set the output directory - use command line argument if provided, otherwise use default
OUTPUTS_DIR = (
    Path(args.output_dir) if args.output_dir else Path(__file__).parent / "outputs"
)
OUTPUTS_DIR.mkdir(exist_ok=True)

print(f"🔍 Starting UMA Early Request Retry - Monitoring for P4 recommendations that haven't expired 🤖 📊")
logger.info(f"Output directory set to: {OUTPUTS_DIR}")

# Dictionary to keep track of requests that we're watching
watched_requests = {}

def get_current_timestamp():
    """Returns the current Unix timestamp as an integer."""
    return int(time.time())

def is_p4_recommendation(output_file_path):
    """Check if the output file contains a P4 recommendation."""
    try:
        with open(output_file_path, "r") as f:
            data = json.load(f)
        return data.get("recommendation", "").lower() == "p4"
    except Exception as e:
        logger.error(f"Error checking recommendation in {output_file_path}: {str(e)}")
        return False

def is_not_expired(output_data):
    """Check if the request has not expired yet."""
    current_timestamp = get_current_timestamp()
    expiration_timestamp = output_data.get("proposal_metadata", {}).get("expiration_timestamp")
    
    if not expiration_timestamp:
        logger.warning(f"No expiration timestamp found for {output_data.get('query_id')}")
        return False
    
    return current_timestamp < expiration_timestamp

def process_output_file(file_path):
    """Process an output file to check if it needs to be retried."""
    try:
        with open(file_path, "r") as f:
            output_data = json.load(f)
        
        query_id = output_data.get("query_id")
        if not query_id:
            logger.warning(f"No query_id found in {file_path}")
            return
        
        # Check if this is a P4 recommendation that hasn't expired
        if output_data.get("recommendation", "").lower() == "p4" and is_not_expired(output_data):
            logger.info(f"Found P4 recommendation that hasn't expired: {query_id}")
            
            # Add to watched requests if not already there
            if query_id not in watched_requests:
                expiration = output_data.get("proposal_metadata", {}).get("expiration_timestamp", 0)
                
                # Get the timestamp of the last response to ensure we wait the minimum time before retrying
                last_response_time = 0
                try:
                    # First check overseer data if it exists
                    if "overseer_data" in output_data and output_data["overseer_data"].get("final_response_metadata"):
                        last_response_time = output_data["overseer_data"]["final_response_metadata"].get("created_timestamp", 0)
                    # Otherwise check standard response metadata
                    elif "response_metadata" in output_data:
                        last_response_time = output_data["response_metadata"].get("created_timestamp", 0)
                    # If no metadata, use file creation time
                    if not last_response_time:
                        last_response_time = int(output_data.get("timestamp", 0))
                except Exception as e:
                    logger.warning(f"Could not determine last response time for {query_id}: {str(e)}")
                    last_response_time = int(time.time())  # Use current time as fallback
                
                watched_requests[query_id] = {
                    "file_path": file_path,
                    "expiration": expiration,
                    "last_retry": last_response_time,  # Initialize with the original response time
                }
                logger.info(f"Added {query_id} to watch list (expires at {expiration}, last response at {datetime.datetime.fromtimestamp(last_response_time).strftime('%Y-%m-%d %H:%M:%S')})")
    except Exception as e:
        logger.error(f"Error processing output file {file_path}: {str(e)}")

def retry_request(query_id, file_path):
    """Retry the request using Perplexity with ChatGPT validation."""
    try:
        with open(file_path, "r") as f:
            output_data = json.load(f)
        
        # Extract the needed information for retrying
        user_prompt = output_data.get("user_prompt")
        system_prompt = output_data.get("system_prompt")
        
        if not user_prompt or not system_prompt:
            logger.error(f"Missing prompt information for {query_id}")
            return False
        
        # Get current timestamp for the system prompt
        current_timestamp = get_current_timestamp()
        current_datetime = datetime.datetime.fromtimestamp(current_timestamp).strftime("%Y-%m-%d %H:%M:%S UTC")
        
        # Update the system prompt timestamp
        updated_system_prompt = system_prompt
        if "Current Unix Timestamp:" in system_prompt:
            updated_system_prompt = "\n".join([
                line if not line.startswith("Current Unix Timestamp:") and not line.startswith("Current Date and Time:") 
                else f"Current Unix Timestamp: {current_timestamp}" if line.startswith("Current Unix Timestamp:") 
                else f"Current Date and Time: {current_datetime}"
                for line in system_prompt.split("\n")
            ])
        
        logger.info(f"Retrying request for {query_id}")
        
        # Call the enhanced Perplexity-ChatGPT loop
        result = enhanced_perplexity_chatgpt_loop(
            user_prompt=user_prompt,
            perplexity_api_key=PERPLEXITY_API_KEY,
            chatgpt_api_key=OPENAI_API_KEY,
            original_system_prompt=updated_system_prompt,
            logger=logger,
            max_attempts=3,
            min_attempts=2,
        )
        
        # Update watched_requests with the retry timestamp
        watched_requests[query_id]["last_retry"] = current_timestamp
        
        # Check if the recommendation changed from P4
        new_recommendation = result.get("final_recommendation")
        changed = new_recommendation.lower() != "p4"
        
        if changed:
            logger.info(f"Recommendation changed from p4 to {new_recommendation} for {query_id}")
            
            # Save the original overseer data
            original_overseer_data = output_data.get("overseer_data", {})
            
            # Update the output data
            output_data["recommendation"] = new_recommendation
            output_data["recommendation_changed"] = True
            output_data["timestamp"] = time.time()
            
            # Create retry data structure
            retry_data = {
                "retry_timestamp": current_timestamp,
                "previous_recommendation": "p4",
                "new_recommendation": new_recommendation,
                "attempts": result["attempts"],
                "interactions": result["responses"],
                "recommendation_journey": [
                    {
                        "attempt": i + 1,
                        "perplexity_recommendation": next(
                            (
                                r["recommendation"]
                                for r in result["responses"]
                                if r.get("attempt") == i + 1
                                and r["interaction_type"] == "perplexity_query"
                            ),
                            None,
                        ),
                        "overseer_satisfaction_level": next(
                            (
                                r["satisfaction_level"]
                                for r in result["responses"]
                                if r.get("stage") == f"evaluation_{i+1}"
                                and r["interaction_type"] == "chatgpt_evaluation"
                            ),
                            None,
                        ),
                        "prompt_updated": next(
                            (
                                r["prompt_updated"]
                                for r in result["responses"]
                                if r.get("stage") == f"evaluation_{i+1}"
                                and r["interaction_type"] == "chatgpt_evaluation"
                            ),
                            False,
                        ),
                        "critique": next(
                            (
                                r["critique"]
                                for r in result["responses"]
                                if r.get("stage") == f"evaluation_{i+1}"
                                and r["interaction_type"] == "chatgpt_evaluation"
                            ),
                            None,
                        ),
                        "system_prompt_before": next(
                            (
                                r["system_prompt_before"]
                                for r in result["responses"]
                                if r.get("stage") == f"evaluation_{i+1}"
                                and r["interaction_type"] == "chatgpt_evaluation"
                            ),
                            None,
                        ),
                        "system_prompt_after": next(
                            (
                                r["system_prompt_after"]
                                for r in result["responses"]
                                if r.get("stage") == f"evaluation_{i+1}"
                                and r["interaction_type"] == "chatgpt_evaluation"
                            ),
                            None,
                        ),
                    }
                    for i in range(result["attempts"])
                ],
            }
            
            # Add the retry data to the output
            if "retry_data" not in output_data:
                output_data["retry_data"] = [retry_data]
            else:
                output_data["retry_data"].append(retry_data)
            
            # Write the updated data back to the file
            with open(file_path, "w") as f:
                json.dump(output_data, f, indent=2)
            
            # Remove from watched requests since we don't need to watch it anymore
            del watched_requests[query_id]
            logger.info(f"Updated output for {query_id} and removed from watch list")
            return True
        else:
            logger.info(f"Recommendation remains p4 for {query_id}")
            return False
        
    except Exception as e:
        logger.error(f"Error retrying request for {query_id}: {str(e)}")
        return False

def check_watched_requests():
    """Check all watched requests to see if they need to be retried or removed."""
    current_timestamp = get_current_timestamp()
    to_remove = []
    
    for query_id, info in watched_requests.items():
        # Check if expired
        if current_timestamp > info["expiration"]:
            logger.info(f"Request {query_id} has expired, removing from watch list")
            to_remove.append(query_id)
            continue
        
        # Check if it's time to retry (check_interval seconds since last retry)
        time_since_last_retry = current_timestamp - info["last_retry"]
        if time_since_last_retry >= args.check_interval:
            time_since_str = f"{time_since_last_retry // 60} minutes, {time_since_last_retry % 60} seconds"
            logger.info(f"Retrying query {query_id} after {time_since_str} (minimum interval: {args.check_interval} seconds)")
            success = retry_request(query_id, info["file_path"])
            if success:
                # If recommendation changed, it will be removed by the retry function
                logger.info(f"Retry for {query_id} resulted in changed recommendation")
            else:
                # Update the last retry timestamp
                watched_requests[query_id]["last_retry"] = current_timestamp
                logger.info(f"Retry for {query_id} completed (no change in recommendation), next retry in {args.check_interval} seconds")
        else:
            # Log how much time remains until next retry (only in debug mode to avoid spam)
            time_remaining = args.check_interval - time_since_last_retry
            logger.debug(f"Next retry for {query_id} in {time_remaining} seconds")
    
    # Remove expired requests
    for query_id in to_remove:
        del watched_requests[query_id]

class OutputFileHandler(FileSystemEventHandler):
    """Handle file system events for output files."""
    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith(".json"):
            logger.info(f"New output file detected: {event.src_path}")
            time.sleep(1)  # Small delay to ensure file is fully written
            process_output_file(event.src_path)
    
    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith(".json"):
            # Check if it's a file we're watching
            file_name = os.path.basename(event.src_path)
            for query_id, info in list(watched_requests.items()):
                if os.path.basename(info["file_path"]) == file_name:
                    logger.info(f"Watched file modified: {file_name}")
                    # Check if recommendation changed
                    if not is_p4_recommendation(event.src_path):
                        logger.info(f"Recommendation changed for {query_id}, removing from watch list")
                        del watched_requests[query_id]
                    break

def scan_output_directory(directory):
    """Scan an output directory for P4 recommendations that haven't expired."""
    logger.info(f"Scanning directory: {directory}")
    for file_path in directory.glob("*.json"):
        process_output_file(file_path)

def scan_results_directories():
    """Scan all experiment output directories in the results folder."""
    results_dir = Path(__file__).parent.parent / "results"
    
    if not results_dir.exists():
        logger.warning(f"Results directory not found: {results_dir}")
        return
    
    for exp_dir in results_dir.iterdir():
        if exp_dir.is_dir() and not exp_dir.name.startswith('.'):
            outputs_dir = exp_dir / "outputs"
            if outputs_dir.exists() and outputs_dir.is_dir():
                logger.info(f"Scanning experiment directory: {exp_dir.name}")
                scan_output_directory(outputs_dir)

def main():
    print("🕙 UMA Early Request Retry - Starting...")
    logger.info("Starting early request retry service")
    
    # Check for valid API keys before processing
    if not PERPLEXITY_API_KEY or not OPENAI_API_KEY:
        logger.error("Missing API keys - cannot proceed")
        print("ERROR: Missing API keys - cannot proceed")
        return
    
    # Initial scan of results directories
    scan_results_directories()
    
    # Set up the file system observer
    observer = Observer()
    
    # Watch the output directory
    observer.schedule(OutputFileHandler(), str(OUTPUTS_DIR), recursive=False)
    
    # Watch the results directory experiment outputs
    results_dir = Path(__file__).parent.parent / "results"
    if results_dir.exists():
        for exp_dir in results_dir.iterdir():
            if exp_dir.is_dir() and not exp_dir.name.startswith('.'):
                outputs_dir = exp_dir / "outputs"
                if outputs_dir.exists() and outputs_dir.is_dir():
                    observer.schedule(OutputFileHandler(), str(outputs_dir), recursive=False)
                    logger.info(f"Watching output directory: {outputs_dir}")
    
    observer.start()
    logger.info("File system observers started")
    
    try:
        while True:
            # Check if any watched requests need to be retried
            check_watched_requests()
            # Sleep for 60 seconds before checking again
            time.sleep(60)
    except KeyboardInterrupt:
        logger.info("Stopping service due to keyboard interrupt")
        observer.stop()
    
    observer.join()
    logger.info("Early request retry service stopped")

if __name__ == "__main__":
    main()