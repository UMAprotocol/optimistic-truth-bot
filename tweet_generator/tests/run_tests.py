#!/usr/bin/env python3
"""
Run all tests for the tweet generator
"""

import unittest
import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

if __name__ == '__main__':
    # Discover and run all tests in the current directory
    test_suite = unittest.defaultTestLoader.discover(os.path.dirname(__file__))
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)
    
    # Exit with non-zero code if tests fail
    sys.exit(not result.wasSuccessful())