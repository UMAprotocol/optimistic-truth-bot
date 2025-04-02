#!/usr/bin/env python3
"""
Validate that a JSON output file contains all required fields for backward compatibility.
This script is used to ensure that multi_operator output files match the expected format.
"""

import os
import sys
import json
import argparse
from pathlib import Path

# Add parent directory to path to allow importing the module
sys.path.insert(0, str(Path(__file__).parent.parent))

from multi_operator.common import validate_output_json


def validate_json_file(file_path):
    """
    Validate that a JSON file contains all required fields.

    Args:
        file_path: Path to the JSON file

    Returns:
        bool: True if valid, False otherwise
    """
    try:
        with open(file_path, "r") as f:
            data = json.load(f)

        valid, missing_fields = validate_output_json(data)

        if valid:
            print(f"✅ {file_path} is valid - contains all required fields")
            return True
        else:
            print(f"❌ {file_path} is missing required fields:")
            for field in missing_fields:
                print(f"  - {field}")
            return False

    except json.JSONDecodeError:
        print(f"❌ {file_path} is not a valid JSON file")
        return False
    except FileNotFoundError:
        print(f"❌ {file_path} does not exist")
        return False
    except Exception as e:
        print(f"❌ Error validating {file_path}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Validate JSON output files for backward compatibility"
    )
    parser.add_argument("file_path", help="Path to the JSON file to validate")
    parser.add_argument("--verbose", action="store_true", help="Show detailed output")

    args = parser.parse_args()

    if args.verbose:
        print(f"Validating {args.file_path}...")

    if validate_json_file(args.file_path):
        if args.verbose:
            print("Validation successful")
        sys.exit(0)
    else:
        if args.verbose:
            print("Validation failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
