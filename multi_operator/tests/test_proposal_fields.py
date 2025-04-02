#!/usr/bin/env python3
"""
Test script to verify all fields from proposals are included in the output.
"""

import os
import json
from pathlib import Path
import sys
import time
import shutil

# Add the root directory to the Python path
current_dir = Path(__file__).parent
module_dir = current_dir.parent

# Import after adjusting the path
try:
    # Try importing as if we're running from the project root
    from multi_operator.proposal_processor import MultiOperatorProcessor
    from multi_operator.common import get_question_id_short, validate_output_json
except ImportError:
    # If that fails, add the parent directory to the path and try again
    sys.path.insert(0, str(current_dir.parent.parent))
    from multi_operator.proposal_processor import MultiOperatorProcessor
    from multi_operator.common import get_question_id_short, validate_output_json


def main():
    # Get the current directory (tests directory)
    tests_dir = Path(__file__).parent.absolute()

    # Create a test output directory within the tests directory
    test_output_dir = tests_dir / "test_output"
    if test_output_dir.exists():
        shutil.rmtree(test_output_dir)
    test_output_dir.mkdir(exist_ok=True)

    print(f"Testing proposal processing with output to {test_output_dir}")

    # Create a test proposals directory within the tests directory
    test_proposals_dir = tests_dir / "test_proposals"
    if test_proposals_dir.exists():
        shutil.rmtree(test_proposals_dir)
    test_proposals_dir.mkdir(exist_ok=True)

    # ... rest of the code ...
