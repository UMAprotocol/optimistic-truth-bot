#!/usr/bin/env python3
"""
Script to find wrong predictions in UMA oracle responses and copy the original proposal files to a target directory.
A prediction is considered wrong if the 'resolved_price_outcome' and 'recommendation' fields do not match.

Example:
    python query_utilities/find_wrong_predictions.py --results-dir results/ --proposals-dir proposals/ --output-dir wrong_predictions/
"""

import argparse
import json
import os
import shutil
import sys
from typing import Dict, List, Any, Optional

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import setup_logging


def load_json_file(file_path: str) -> Optional[Dict[str, Any]]:
    """Load and parse a JSON file."""
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading {file_path}: {e}")
        return None


def find_wrong_predictions(
    results_dir: str, proposals_dir: str, output_dir: str
) -> int:
    """
    Find wrong predictions and copy the original proposal files to the output directory.

    Args:
        results_dir: Directory containing result files
        proposals_dir: Directory containing original proposal files
        output_dir: Directory to copy wrong prediction proposals to

    Returns:
        Number of wrong predictions found
    """
    logger = setup_logging("find_wrong_predictions", "find_wrong_predictions.log")

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    wrong_count = 0
    processed_count = 0

    # Process each JSON file in the results directory
    for filename in os.listdir(results_dir):
        if not filename.endswith(".json"):
            continue

        result_path = os.path.join(results_dir, filename)
        result_data = load_json_file(result_path)

        if not result_data:
            logger.warning(f"Skipping {filename}: Unable to load file")
            continue

        processed_count += 1

        # Extract the necessary fields
        resolved_price_outcome = result_data.get("resolved_price_outcome")
        recommendation = result_data.get("recommendation")
        processed_file = result_data.get("processed_file")
        question_id = result_data.get("question_id_short")

        # Check if prediction is wrong (recommendation doesn't match resolved outcome)
        if (
            resolved_price_outcome
            and recommendation
            and resolved_price_outcome != recommendation
        ):
            wrong_count += 1
            logger.info(
                f"Wrong prediction found in {filename}: {resolved_price_outcome} vs {recommendation}"
            )

            # Find and copy the proposal file
            if processed_file:
                proposal_path = os.path.join(proposals_dir, processed_file)
                if os.path.exists(proposal_path):
                    output_path = os.path.join(output_dir, processed_file)
                    shutil.copy2(proposal_path, output_path)
                    logger.info(f"Copied {processed_file} to {output_dir}")
                else:
                    logger.warning(f"Proposal file not found: {proposal_path}")
            else:
                # If processed_file is not available, try using question_id
                if question_id:
                    proposal_filename = f"questionId_{question_id}.json"
                    proposal_path = os.path.join(proposals_dir, proposal_filename)
                    if os.path.exists(proposal_path):
                        output_path = os.path.join(output_dir, proposal_filename)
                        shutil.copy2(proposal_path, output_path)
                        logger.info(f"Copied {proposal_filename} to {output_dir}")
                    else:
                        logger.warning(f"Proposal file not found: {proposal_path}")
                else:
                    logger.warning(f"No proposal file info found in {filename}")

    logger.info(
        f"Processed {processed_count} results, found {wrong_count} wrong predictions"
    )
    print(f"Processed {processed_count} results, found {wrong_count} wrong predictions")
    print(f"Wrong predictions copied to {output_dir}")

    return wrong_count


def main():
    """Main function to parse arguments and find wrong predictions."""
    parser = argparse.ArgumentParser(
        description="Find wrong predictions in UMA oracle responses and copy original proposal files."
    )
    parser.add_argument(
        "--results-dir",
        required=True,
        help="Directory containing result files (like 25b74cfb.json)",
    )
    parser.add_argument(
        "--proposals-dir",
        required=True,
        help="Directory containing original proposal files (like questionId_25b74cfb.json)",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Directory to copy wrong prediction proposals to",
    )

    args = parser.parse_args()

    return (
        0
        if find_wrong_predictions(args.results_dir, args.proposals_dir, args.output_dir)
        >= 0
        else 1
    )


if __name__ == "__main__":
    sys.exit(main())
