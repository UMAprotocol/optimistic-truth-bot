# Multi-Operator Tests

This directory contains test files and utilities for validating the Multi-Operator's output formats and functionality.

## Directory Structure

- `test_output/` - Contains generated output files from test runs
- `test_proposals/` - Contains sample proposal files used for testing
- `test_proposal_fields.py` - Script to test that output files contain all required fields
- `validate_json_format.py` - Utility to validate JSON output against required field specifications

## Running Tests

To verify the output format compatibility:

```bash
# Run from the main multi_operator directory:
python -m tests.test_proposal_fields

# To validate a specific JSON output file:
python -m tests.validate_json_format path/to/output.json --verbose
```

## Expected Output Format

The Multi-Operator output format is designed to be backward compatible with the previous implementation while providing additional information for the multi-operator flow. Key requirements include:

1. Essential fields must be present at the top level (query_id, recommendation, etc.)
2. Fields like `icon` and `condition_id` must be at the top level only
3. `transaction_hash` must be in `proposal_metadata` only 
4. Fields like tags, prices, etc. are duplicated at both levels for compatibility
5. The `recommendation` field must contain the final p1/p2/p3/p4 value 