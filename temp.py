#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path


def merge_proposal_data(result_file_path):
    """
    Reads a result file and the associated proposal file, then merges the proposal data
    into the result file.

    Args:
        result_file_path: Path to the result file (e.g., 0a686fea.json)
    """
    # Load the result file
    with open(result_file_path, "r") as f:
        result_data = json.load(f)

    # Get the processed file name from the result data
    if "processed_file" not in result_data:
        print(f"Error: 'processed_file' field not found in {result_file_path}")
        return False

    processed_file = result_data["processed_file"]

    # Locate the proposal file in the proposals/updated_metadata directory
    proposal_file_path = os.path.join("proposals", "updated_metadata", processed_file)
    if not os.path.exists(proposal_file_path):
        print(f"Error: Proposal file not found at {proposal_file_path}")
        return False

    # Load the proposal file
    with open(proposal_file_path, "r") as f:
        proposal_data = json.load(f)

    # Proposal files contain an array, get the first item
    if isinstance(proposal_data, list) and len(proposal_data) > 0:
        proposal_data = proposal_data[0]

    # Initialize proposal_metadata if it doesn't exist
    if "proposal_metadata" not in result_data:
        result_data["proposal_metadata"] = {}

    # Handle unix_timestamp / request_timestamp equivalence
    if "unix_timestamp" in proposal_data:
        proposal_data["request_timestamp"] = proposal_data["unix_timestamp"]
        del proposal_data["unix_timestamp"]

    # Remove unix_timestamp from the result data if it exists
    if "unix_timestamp" in result_data:
        del result_data["unix_timestamp"]

    # Transaction-related fields to be placed in proposal_metadata
    transaction_fields = [
        "transaction_hash",
        "block_number",
        "request_transaction_block_time",
        "ancillary_data_hex",
        "request_timestamp",
        "expiration_timestamp",
        "creator",
        "proposer",
        "bond_currency",
        "proposal_bond",
        "reward_amount",
        "condition_id",
        "updates",
    ]

    # Copy transaction-related fields to proposal_metadata
    for field in transaction_fields:
        if field in proposal_data and field not in result_data["proposal_metadata"]:
            result_data["proposal_metadata"][field] = proposal_data[field]

    # Remove transaction_hash from the base level if it exists
    if "transaction_hash" in result_data:
        del result_data["transaction_hash"]

    # Fields to be placed at the top level
    top_level_fields = ["icon", "tags", "end_date_iso", "game_start_time"]

    # Copy top-level fields
    for field in top_level_fields:
        if field in proposal_data and field not in result_data:
            result_data[field] = proposal_data[field]

    # Save the augmented result file
    with open(result_file_path, "w") as f:
        json.dump(result_data, f, indent=2)

    print(f"Successfully merged proposal data into {result_file_path}")
    return True


def process_all_results(results_dir):
    """
    Process all result files in the specified directory.

    Args:
        results_dir: Directory containing result files
    """
    success_count = 0
    failure_count = 0

    for root, _, files in os.walk(results_dir):
        for file in files:
            if file.endswith(".json"):
                file_path = os.path.join(root, file)
                print(f"Processing {file_path}...")

                if merge_proposal_data(file_path):
                    success_count += 1
                else:
                    failure_count += 1

    print(
        f"Processing complete. {success_count} files updated successfully, {failure_count} failed."
    )


def main():
    if len(sys.argv) > 1:
        # Process a single file
        merge_proposal_data(sys.argv[1])
    else:
        # Default: process all files in the results directory
        results_dir = "results"
        for subdir in os.listdir(results_dir):
            subdir_path = os.path.join(results_dir, subdir)
            if os.path.isdir(subdir_path) and "outputs" in os.listdir(subdir_path):
                outputs_path = os.path.join(subdir_path, "outputs")
                process_all_results(outputs_path)


if __name__ == "__main__":
    main()
