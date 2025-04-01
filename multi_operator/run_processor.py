#!/usr/bin/env python3
"""
Run the UMA Multi-Operator Proposal Processor.

This script is a simple wrapper to run the MultiOperatorProcessor
from the command line.
"""

import sys
import os

# Add the parent directory to the path so we can import the module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the main function from proposal_processor
from multi_operator.proposal_processor import main

if __name__ == "__main__":
    main()
