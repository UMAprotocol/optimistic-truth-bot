#!/usr/bin/env python3
"""
Run the UMA Multi-Operator Early Request Retry Service.

This script is a simple wrapper to run the Multi-Operator Early Request Retry
from the command line.
"""

import sys
import os

# Add the parent directory to the path so we can import the module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the main function from early_request_retry
from multi_operator.early_request_retry import main

if __name__ == "__main__":
    main()