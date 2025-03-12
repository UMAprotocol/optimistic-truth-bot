#!/usr/bin/env python3
"""
UMA Output Converter - Converts existing output files to the new format.
- Removes unnecessary fields (resolution_description, is_finalized, etc.)
- Restructures raw_proposal_data into proposal_metadata
- Adds resolution_tx field if missing

Usage: python proposal_replayer/output_converter.py
"""

import os
import json
import sys
from pathlib import Path
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("output_converter")

# Directory paths
CURRENT_DIR = Path(__file__).parent
OUTPUTS_DIR = CURRENT_DIR / "outputs"


def convert_output_file(file_path):
    """Convert a single output file to the new format."""
    try:
        with open(file_path, "r") as f:
            data = json.load(f)

        # Track if any changes were made
        changes_made = False

        # Remove unnecessary fields
        fields_to_remove = [
            "resolution_description",
            "is_finalized",
            "finalized_timestamp",
            "finalized_datetime",
        ]

        for field in fields_to_remove:
            if field in data:
                data.pop(field)
                changes_made = True
                logger.debug(f"Removed field: {field}")

        # Add resolution_tx if missing
        if "resolution_tx" not in data:
            data["resolution_tx"] = None
            changes_made = True
            logger.debug("Added resolution_tx field")

        # Restructure raw_proposal_data if present
        if "raw_proposal_data" in data and "proposal_metadata" not in data:
            raw_data = data.pop("raw_proposal_data")
            changes_made = True

            if isinstance(raw_data, list) and len(raw_data) > 0:
                raw_data = raw_data[0]

            # Create a cleaner proposal_metadata structure
            data["proposal_metadata"] = {
                "creator": raw_data.get("creator", ""),
                "proposal_bond": raw_data.get("proposal_bond", 0),
                "reward_amount": raw_data.get("reward_amount", 0),
                "unix_timestamp": raw_data.get("unix_timestamp", 0),
                "block_number": raw_data.get("block_number", 0),
                "updates": raw_data.get("updates", []),
                "ancillary_data_hex": raw_data.get("ancillary_data_hex", ""),
            }
            logger.debug("Restructured raw_proposal_data into proposal_metadata")

        # Save the file if changes were made
        if changes_made:
            with open(file_path, "w") as f:
                json.dump(data, f, indent=2)
            logger.info(f"Updated file: {file_path.name}")
            return True
        else:
            logger.info(f"No changes needed for file: {file_path.name}")
            return False

    except Exception as e:
        logger.error(f"Error processing {file_path.name}: {str(e)}")
        return False


def process_all_outputs():
    """Process all output files in the directory."""
    if not OUTPUTS_DIR.exists():
        logger.error(f"Outputs directory not found: {OUTPUTS_DIR}")
        return

    processed_count = 0
    updated_count = 0
    error_count = 0

    for output_file in OUTPUTS_DIR.glob("*.json"):
        processed_count += 1

        try:
            if convert_output_file(output_file):
                updated_count += 1
        except Exception as e:
            logger.error(f"Error converting {output_file.name}: {str(e)}")
            error_count += 1

    logger.info(
        f"Processing complete. Processed: {processed_count}, Updated: {updated_count}, Errors: {error_count}"
    )


def main():
    logger.info("Starting UMA Output Converter")
    process_all_outputs()
    logger.info("Conversion completed")


if __name__ == "__main__":
    main()
