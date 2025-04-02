#!/bin/bash
# Script to run all multi_operator tests

echo "Running multi_operator tests..."
python -m tests.run_tests

# Exit with the status code from the tests
exit $? 