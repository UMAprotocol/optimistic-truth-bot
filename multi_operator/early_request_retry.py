#!/usr/bin/env python3
"""
UMA Multi-Operator Early Request Retry - Monitors outputs for P4 recommendations that have not expired and retries them.
Usage: python multi_operator/early_request_retry.py [--output-dir PATH] [--check-interval SECONDS]
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
import importlib
from dotenv import load_dotenv

# Add the parent directory to the path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import MultiOperatorProcessor components
from multi_operator.proposal_processor import MultiOperatorProcessor
from multi_operator.common import (
    setup_logging,
    get_question_id_short,
)

# Parse command line arguments
parser = argparse.ArgumentParser(
    description="UMA Multi-Operator Early Request Retry - Monitor for P4 recommendations that haven't expired"
)

parser.add_argument(
    "--output-dir", type=str, help="Directory to monitor for output files"
)

parser.add_argument(
    "--proposals-dir", type=str, help="Directory containing proposal JSON files", default="proposals"
)

parser.add_argument(
    "--check-interval", 
    type=int, 
    default=300, 
    help="Time in seconds between checks for expired requests (default: 300)"
)

parser.add_argument(
    "--verbose",
    action="store_true",
    help="Enable verbose output with detailed logs",
)

args = parser.parse_args()

# Setup logging
logger = setup_logging("multi_operator_early_retry", "logs/multi_operator_early_retry.log")
load_dotenv()

# Verify API keys are available
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not PERPLEXITY_API_KEY:
    logger.error("PERPLEXITY_API_KEY not found in environment variables")
    sys.exit(1)

if not OPENAI_API_KEY:
    logger.error("OPENAI_API_KEY not found in environment variables")
    sys.exit(1)

# Set the output directory - use command line argument if provided, otherwise use default
OUTPUTS_DIR = Path(args.output_dir) if args.output_dir else Path("results/latest/outputs")
OUTPUTS_DIR.mkdir(exist_ok=True, parents=True)

# Dictionary to keep track of requests that we're watching
watched_requests = {}

# Initialize processor instance (will be lazy-loaded when needed)
processor = None


def get_processor():
    """Get or initialize the MultiOperatorProcessor."""
    global processor
    if processor is None:
        logger.info("Initializing MultiOperatorProcessor...")
        processor = MultiOperatorProcessor(
            proposals_dir=args.proposals_dir,
            output_dir=args.output_dir,
            max_attempts=3,
            min_attempts=2,
            verbose=args.verbose,
        )
    return processor


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
    
    # Check multiple possible locations for expiration timestamp in the data structure
    expiration_timestamp = None
    
    # Try proposal_metadata first
    if "proposal_metadata" in output_data:
        expiration_timestamp = output_data["proposal_metadata"].get("expiration_timestamp")
    
    # If not found, check other locations
    if not expiration_timestamp and "expiration_timestamp" in output_data:
        expiration_timestamp = output_data["expiration_timestamp"]
    
    # For backward compatibility with other structure formats
    if not expiration_timestamp and isinstance(output_data.get("proposal_metadata"), list) and len(output_data["proposal_metadata"]) > 0:
        expiration_timestamp = output_data["proposal_metadata"][0].get("expiration_timestamp")
    
    if not expiration_timestamp:
        logger.warning(f"No expiration timestamp found for {output_data.get('query_id', 'unknown')}")
        return False
    
    # Check if current time is less than expiration timestamp
    return current_timestamp < expiration_timestamp


def process_output_file(file_path):
    """Process an output file to check if it needs to be retried."""
    try:
        with open(file_path, "r") as f:
            output_data = json.load(f)
        
        # Extract query_id
        query_id = output_data.get("query_id", "")
        if not query_id:
            # Try using short_id if available
            short_id = output_data.get("short_id") or output_data.get("question_id_short", "")
            if short_id:
                query_id = short_id  # Use short_id as fallback
            else:
                logger.warning(f"No query_id found in {file_path}")
                return
        
        # Get short_id for more readable logs
        short_id = get_question_id_short(query_id)
        
        # Check if this is a P4 recommendation that hasn't expired
        if output_data.get("recommendation", "").lower() == "p4" and is_not_expired(output_data):
            logger.info(f"Found P4 recommendation that hasn't expired: {short_id}")
            
            # Add to watched requests if not already there
            if short_id not in watched_requests:
                # Get expiration timestamp
                expiration = None
                if "proposal_metadata" in output_data:
                    expiration = output_data["proposal_metadata"].get("expiration_timestamp")
                if not expiration and "expiration_timestamp" in output_data:
                    expiration = output_data["expiration_timestamp"]
                
                # Get the timestamp of the last response to ensure we wait the minimum time before retrying
                last_response_time = 0
                try:
                    # Check for the timestamp in various locations
                    if "timestamp" in output_data:
                        last_response_time = int(output_data["timestamp"])
                    elif "response_metadata" in output_data:
                        last_response_time = output_data["response_metadata"].get("created_timestamp", 0)
                    elif "solver_results" in output_data and output_data["solver_results"]:
                        for result in output_data["solver_results"]:
                            if "response_metadata" in result:
                                last_response_time = result["response_metadata"].get("created_timestamp", 0)
                                if last_response_time:
                                    break
                                    
                    # If no timestamp found, use current time
                    if not last_response_time:
                        last_response_time = get_current_timestamp()
                        
                except Exception as e:
                    logger.warning(f"Could not determine last response time for {short_id}: {str(e)}")
                    last_response_time = get_current_timestamp()  # Use current time as fallback
                
                # Get the original file path to the proposal
                original_file_path = None
                if "file_path" in output_data:
                    original_file_path = output_data.get("file_path")
                elif "processed_file" in output_data:
                    # Try to find the original file in proposals directory
                    processed_file = output_data.get("processed_file")
                    proposals_dir = Path(args.proposals_dir)
                    potential_file = proposals_dir / processed_file
                    if potential_file.exists():
                        original_file_path = str(potential_file)
                    else:
                        # Try to find by query_id pattern
                        for p_file in proposals_dir.glob("**/*.json"):
                            if short_id.lower() in p_file.name.lower():
                                original_file_path = str(p_file)
                                break
                
                # If we can't find the original proposal file, we can't retry
                if not original_file_path:
                    logger.warning(f"Could not find original proposal file for {short_id}, skipping retry")
                    return
                
                # For newly detected files, set the last_retry to current time
                # This ensures we wait a full check_interval before the first retry
                # since we assume the multi_operator just ran on this file
                current_time = get_current_timestamp()
                
                watched_requests[short_id] = {
                    "output_file_path": file_path,
                    "proposal_file_path": original_file_path, 
                    "expiration": expiration,
                    "last_retry": current_time,  # Use current time instead of file timestamp
                    "user_prompt": output_data.get("user_prompt", ""),
                    "system_prompt": output_data.get("system_prompt", ""),
                    "original_timestamp": last_response_time,  # Store original timestamp for reference
                }
                
                next_retry_time = datetime.datetime.fromtimestamp(current_time + args.check_interval).strftime('%Y-%m-%d %H:%M:%S')
                logger.info(f"Added {short_id} to watch list (expires at {expiration}, original response at {datetime.datetime.fromtimestamp(last_response_time).strftime('%Y-%m-%d %H:%M:%S')}, next retry at {next_retry_time})")
                
                if args.verbose:
                    expiration_date = datetime.datetime.fromtimestamp(expiration).strftime('%Y-%m-%d %H:%M:%S') if expiration else "unknown"
                    original_date = datetime.datetime.fromtimestamp(last_response_time).strftime('%Y-%m-%d %H:%M:%S')
                    print(f"⏰ Added {short_id} to watch list")
                    print(f"  - Expires at: {expiration_date}")
                    print(f"  - Original response at: {original_date}")
                    print(f"  - Next retry at: {next_retry_time}")
                    print(f"  - Original file: {original_file_path}")
                    print(f"  - Output file: {file_path}")
    except Exception as e:
        logger.error(f"Error processing output file {file_path}: {str(e)}")


def retry_request(short_id, info):
    """Retry the request using the MultiOperatorProcessor."""
    try:
        logger.info(f"Retrying request for {short_id}")
        
        # Load the original proposal file
        try:
            with open(info["proposal_file_path"], "r") as f:
                proposal_data = json.load(f)
        except Exception as e:
            logger.error(f"Failed to read proposal file {info['proposal_file_path']}: {str(e)}")
            return False
        
        # Get the MultiOperatorProcessor
        proc = get_processor()
        
        # Create proposal_info dictionary for processing
        proposal_info = {
            "file_path": Path(info["proposal_file_path"]),
            "proposal_data": proposal_data,
            "query_id": short_id,  # Using short_id as query_id since we use it as the key
            "short_id": short_id,
        }
        
        # Process the proposal with the processor
        result = proc.process_proposal(proposal_info)
        
        # Update watched_requests with the retry timestamp
        watched_requests[short_id]["last_retry"] = get_current_timestamp()
        
        # Check if the recommendation changed from P4
        if result:
            new_recommendation = result.get("recommendation", "").lower()
            changed = new_recommendation != "p4"
            
            if changed:
                logger.info(f"Recommendation changed from p4 to {new_recommendation} for {short_id}")
                # Remove from watched requests since we don't need to watch it anymore
                del watched_requests[short_id]
                return True
            else:
                logger.info(f"Recommendation remains p4 for {short_id}")
                return False
        else:
            logger.error(f"Failed to process proposal for {short_id}")
            return False
            
    except Exception as e:
        logger.error(f"Error retrying request for {short_id}: {str(e)}")
        return False


def check_watched_requests():
    """Check all watched requests to see if they need to be retried or removed."""
    current_timestamp = get_current_timestamp()
    to_remove = []
    
    for short_id, info in watched_requests.items():
        # Check if expired
        if current_timestamp > info["expiration"]:
            logger.info(f"Request {short_id} has expired, removing from watch list")
            to_remove.append(short_id)
            continue
        
        # Check if it's time to retry (check_interval seconds since last retry)
        time_since_last_retry = current_timestamp - info["last_retry"]
        if time_since_last_retry >= args.check_interval:
            time_since_str = f"{time_since_last_retry // 60} minutes, {time_since_last_retry % 60} seconds"
            logger.info(f"Retrying query {short_id} after {time_since_str} (minimum interval: {args.check_interval} seconds)")
            
            if args.verbose:
                print(f"🔄 Retrying query {short_id} after {time_since_str}")
                
            success = retry_request(short_id, info)
            if success:
                # If recommendation changed, it will be removed by the retry function
                logger.info(f"Retry for {short_id} resulted in changed recommendation")
                if args.verbose:
                    print(f"✅ Retry for {short_id} resulted in changed recommendation - removed from watch list")
            else:
                # Update the last retry timestamp
                watched_requests[short_id]["last_retry"] = current_timestamp
                logger.info(f"Retry for {short_id} completed (no change in recommendation), next retry in {args.check_interval} seconds")
                if args.verbose:
                    print(f"⏳ No change in recommendation for {short_id}, next retry in {args.check_interval} seconds")
        else:
            # Log how much time remains until next retry (only in debug mode to avoid spam)
            time_remaining = args.check_interval - time_since_last_retry
            logger.debug(f"Next retry for {short_id} in {time_remaining} seconds")
    
    # Remove expired requests
    for short_id in to_remove:
        del watched_requests[short_id]
        if args.verbose:
            print(f"⌛ Request {short_id} has expired, removed from watch list")


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
            for short_id, info in list(watched_requests.items()):
                if os.path.basename(info["output_file_path"]) == file_name:
                    logger.info(f"Watched file modified: {file_name}")
                    # Check if recommendation changed
                    if not is_p4_recommendation(event.src_path):
                        logger.info(f"Recommendation changed for {short_id}, removing from watch list")
                        del watched_requests[short_id]
                        if args.verbose:
                            print(f"✅ Recommendation changed for {short_id}, removed from watch list")
                    break


def scan_output_directory(directory):
    """Scan an output directory for P4 recommendations that haven't expired."""
    logger.info(f"Scanning directory: {directory}")
    if args.verbose:
        print(f"🔍 Scanning directory: {directory}")
        
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
    print("🕙 UMA Multi-Operator Early Request Retry - Starting...")
    logger.info("Starting multi-operator early request retry service")
    
    # Check for valid API keys before processing
    if not PERPLEXITY_API_KEY or not OPENAI_API_KEY:
        logger.error("Missing API keys - cannot proceed")
        print("ERROR: Missing API keys - cannot proceed")
        return
    
    # Initial scan of the output directory
    scan_output_directory(OUTPUTS_DIR)
    
    # Also scan results directories
    scan_results_directories()
    
    # Set up the file system observer
    observer = Observer()
    
    # Watch the output directory
    observer.schedule(OutputFileHandler(), str(OUTPUTS_DIR), recursive=False)
    logger.info(f"Watching output directory: {OUTPUTS_DIR}")
    
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
    
    if args.verbose:
        print("\n" + "=" * 80)
        print("\033[1m\033[36m")
        print("  _   _ __  __    _                      _             ___       _               ")
        print(" | | | |  \/  |  / \     _ __ ___  _   _| |_          |_ _|_ __ | |_ ___ _ __ _ __  ___ _ __ ")
        print(" | | | | |\/| | / _ \   | '_ ` _ \| | | | __|  _____   | || '_ \| __/ _ \ '__| '_ \/ __| '_ \ ")
        print(" | |_| | |  | |/ ___ \  | | | | | | |_| | |_  |_____|  | || | | | ||  __/ |  | |_) \__ \ |_) |")
        print("  \___/|_|  |_/_/   \_\ |_| |_| |_|\__,_|\__|         |___|_| |_|\__\___|_|  | .__/|___/ .__/ ")
        print("                                                                            |_|       |_|    ")
        print("\033[0m")
        print("  Multi-Operator Early Request Retry Service")
        print(f"  Check Interval: {args.check_interval}s | Output Dir: {OUTPUTS_DIR}")
        print("=" * 80 + "\n")
        
        # Create a box around the monitoring message
        box_width = 80
        message = f"📡 Monitoring for P4 recommendations that haven't expired... [Press Ctrl+C to stop]"
        padding = (box_width - len(message) - 12) // 2
        print("┌" + "─" * (box_width - 2) + "┐")
        print("│" + " " * padding + message + " " * padding + "│")
        print("└" + "─" * (box_width - 2) + "┘\n")
    
    try:
        while True:
            # Check if any watched requests need to be retried
            check_watched_requests()
            # Sleep for 60 seconds before checking again
            time.sleep(60)
    except KeyboardInterrupt:
        logger.info("Stopping service due to keyboard interrupt")
        observer.stop()
        if args.verbose:
            print("\n\033[1m\033[33m⚠️  Shutting down gracefully, please wait...\033[0m")
    
    observer.join()
    logger.info("Multi-operator early request retry service stopped")
    if args.verbose:
        print("\033[1m\033[32m✅ Shutdown complete\033[0m")


if __name__ == "__main__":
    main()