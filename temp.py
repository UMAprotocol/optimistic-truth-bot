#!/usr/bin/env python3

import json
import os
import argparse
from pathlib import Path
import logging
import sys
import shutil

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def process_file(file_path, processed_files_dir, output_dir):
    """
    Process a single JSON file by retrieving fields from its processed_file.

    Args:
        file_path (Path): Path to the JSON file to process
        processed_files_dir (Path): Directory containing processed files
        output_dir (Path): Directory to write updated files to

    Returns:
        bool: True if file was successfully updated, False otherwise
    """
    try:
        # Read the original file
        with open(file_path, "r") as f:
            data = json.load(f)

        # Create output file path preserving the same filename
        output_file_path = output_dir / file_path.name

        # Check if the file has a processed_file field
        if "processed_file" not in data:
            logger.warning(
                f"File {file_path} does not have a processed_file field, copying to output unchanged."
            )
            shutil.copy2(file_path, output_file_path)
            return False

        processed_file_name = data["processed_file"]
        processed_file_path = processed_files_dir / processed_file_name

        # Check if the processed file exists
        if not processed_file_path.exists():
            logger.warning(
                f"Processed file {processed_file_path} not found, copying to output unchanged."
            )
            shutil.copy2(file_path, output_file_path)
            return False

        # Read the processed file
        with open(processed_file_path, "r") as f:
            processed_data = json.load(f)

        # Process as a list (some files contain arrays of objects)
        if isinstance(processed_data, list):
            if len(processed_data) > 0:
                processed_data = processed_data[0]  # Take the first item if it's a list
            else:
                logger.warning(
                    f"Processed file {processed_file_path} contains an empty list, copying to output unchanged."
                )
                shutil.copy2(file_path, output_file_path)
                return False

        # Fields to check and copy from processed file to main file
        fields_to_update = []

        # Fields that should be at the root level
        root_fields = [
            "tags",
            "icon",
            "end_date_iso",
            "game_start_time",
        ]

        # Add root level fields
        for field in root_fields:
            if field in processed_data and field not in data:
                data[field] = processed_data[field]
                fields_to_update.append(field)

        # Check specifically for proposal_metadata fields that might be missing
        if "proposal_metadata" in data:
            # Fields that should be within proposal_metadata
            proposal_metadata_fields = [
                "creator",
                "proposal_bond",
                "reward_amount",
                "unix_timestamp",
                "block_number",
                "updates",
                "ancillary_data_hex",
                "transaction_hash",
                "request_transaction_block_time",
                "request_timestamp",
                "expiration_timestamp",
                "proposer",
                "bond_currency",
                "condition_id",
            ]

            proposal_metadata = data["proposal_metadata"]

            # Update proposal_metadata fields
            for field in proposal_metadata_fields:
                # Check if field exists in processed data (could be at root or in processed data)
                if field not in proposal_metadata:
                    if field in processed_data:
                        proposal_metadata[field] = processed_data[field]
                        fields_to_update.append(f"proposal_metadata.{field}")
                    # Some fields might be nested in a different structure in the processed file
                    elif field == "condition_id" and "condition_id" in processed_data:
                        proposal_metadata[field] = processed_data["condition_id"]
                        fields_to_update.append(f"proposal_metadata.{field}")

            # Special case: Set unix_timestamp to be equal to request_timestamp if it exists
            if "request_timestamp" in processed_data:
                proposal_metadata["unix_timestamp"] = processed_data[
                    "request_timestamp"
                ]
                if "unix_timestamp" not in fields_to_update:
                    fields_to_update.append(f"proposal_metadata.unix_timestamp")

        # If no fields were updated, copy the original file and log
        if not fields_to_update:
            logger.info(
                f"No fields needed to be updated in {file_path.name}, copying to output unchanged."
            )
            shutil.copy2(file_path, output_file_path)
            return False

        # Write the updated data to the output file
        with open(output_file_path, "w") as f:
            json.dump(data, f, indent=2)

        logger.info(
            f"Updated {file_path.name} with fields: {', '.join(fields_to_update)}"
        )
        return True

    except Exception as e:
        logger.error(f"Error processing file {file_path}: {str(e)}")
        return False


def process_directory(directory_path, processed_files_dir, output_dir):
    """
    Process all JSON files in a directory.

    Args:
        directory_path (Path): Path to directory containing JSON files to process
        processed_files_dir (Path): Directory containing processed files
        output_dir (Path): Directory to write updated files to

    Returns:
        tuple: (processed_count, updated_count, error_count)
    """
    processed_count = 0
    updated_count = 0
    error_count = 0

    # Ensure the directories exist
    if not directory_path.exists():
        logger.error(f"Directory not found: {directory_path}")
        return 0, 0, 0

    if not processed_files_dir.exists():
        logger.error(f"Processed files directory not found: {processed_files_dir}")
        return 0, 0, 0

    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)

    # Process all JSON files in the directory
    for file_path in directory_path.glob("*.json"):
        processed_count += 1

        try:
            if process_file(file_path, processed_files_dir, output_dir):
                updated_count += 1
        except Exception as e:
            logger.error(f"Error processing {file_path.name}: {str(e)}")
            error_count += 1

    logger.info(
        f"Processed {processed_count} files, updated {updated_count}, errors: {error_count}"
    )
    return processed_count, updated_count, error_count


def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Update JSON files with fields from their processed files"
    )
    parser.add_argument("directory", help="Directory containing JSON files to process")
    parser.add_argument(
        "processed_files_dir", help="Directory containing processed files"
    )
    parser.add_argument("output_dir", help="Directory to write updated files to")

    args = parser.parse_args()

    # Convert paths to Path objects
    directory_path = Path(args.directory)
    processed_files_dir = Path(args.processed_files_dir)
    output_dir = Path(args.output_dir)

    # Process the directory
    processed, updated, errors = process_directory(
        directory_path, processed_files_dir, output_dir
    )

    if errors > 0:
        logger.warning(f"Completed with {errors} errors")
        return 1
    else:
        logger.info(
            f"Successfully processed {processed} files, updated {updated} files to {output_dir}"
        )
        return 0


if __name__ == "__main__":
    sys.exit(main())
