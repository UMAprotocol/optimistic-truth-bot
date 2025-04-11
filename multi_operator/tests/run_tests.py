#!/usr/bin/env python3
"""
Test runner for multi_operator validation.
This script runs all tests to ensure the multi_operator output is correct.
"""

import os
import sys
import json
import shutil
from pathlib import Path

# Get the current directory and add the root to the Python path
current_dir = Path(__file__).parent
root_dir = current_dir.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from multi_operator.proposal_processor import MultiOperatorProcessor
from multi_operator.common import get_question_id_short, validate_output_json


def setup_test_dirs():
    """Set up test directories for output and proposals."""
    # Create test output directory
    test_output_dir = current_dir / "test_output"
    if test_output_dir.exists():
        shutil.rmtree(test_output_dir)
    test_output_dir.mkdir(exist_ok=True)

    # Create test proposals directory
    test_proposals_dir = current_dir / "test_proposals"
    if test_proposals_dir.exists():
        shutil.rmtree(test_proposals_dir)
    test_proposals_dir.mkdir(exist_ok=True)

    return test_output_dir, test_proposals_dir


def create_test_proposal(test_proposals_dir):
    """Create a sample test proposal file."""
    # Create a sample proposal
    sample_proposal = [
        {
            "query_id": "0xe5373cc54eb12bc20210bbc945d0eb96881c6bdd90057b67abe6958bcce77a9d",
            "transaction_hash": "0xde871f58887ef3e98ef9f941df53ccd32766eaa3acb6800535564d2482c323b6",
            "block_number": 69125278,
            "request_transaction_block_time": 1742140865,
            "ancillary_data": "Sample ancillary data",
            "ancillary_data_hex": "0x73616d706c65",
            "resolution_conditions": "res_data:p1: 0, p2: 1, p3: 0.5.",
            "proposed_price": 0,
            "proposed_price_outcome": "p1",
            "resolved_price": None,
            "resolved_price_outcome": None,
            "request_timestamp": 1741964809,
            "expiration_timestamp": 1742148065,
            "creator": "0x6A9D222616C90FcA5754cd1333cFD9b7fb6a4F74",
            "proposer": "0xcf12F5b99605CB299Fb11d5EfF4fB304De008d02",
            "bond_currency": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
            "proposal_bond": 500000000,
            "reward_amount": 5000000,
            "updates": [],
            "condition_id": "0x0ecdbc27eda94366284bf4c8e990017491d57f95c53dcd2353d6104ff7cb9e54",
            "tags": ["Crypto", "Bitcoin", "Crypto Prices", "Recurring"],
            "icon": "https://polymarket-upload.s3.us-east-2.amazonaws.com/bitcoin-up-or-down.jpg",
            "end_date_iso": "2025-03-16T00:00:00Z",
            "game_start_time": None,
            "disputer_address": "0xdf08FFC4619e0324B3d38F85d5F07A5Cf31f133F",
        }
    ]

    # Write the proposal to a file
    test_proposal_file = test_proposals_dir / "questionId_e5373cc5.json"
    with open(test_proposal_file, "w") as f:
        json.dump(sample_proposal, f, indent=2)

    print(f"Created test proposal file: {test_proposal_file}")
    return test_proposal_file, sample_proposal


def create_mock_result(test_proposal_file, sample_proposal):
    """Create a mock result for testing."""
    mock_query_id = "0xe5373cc54eb12bc20210bbc945d0eb96881c6bdd90057b67abe6958bcce77a9d"
    mock_short_id = get_question_id_short(mock_query_id)

    # Define the solver results
    solver_results = [
        {
            "solver": "perplexity",
            "recommendation": "p2",
            "response": "Test response",
            "attempt": 1,
            "execution_successful": True,
            "overseer_result": {
                "decision": {
                    "verdict": "SATISFIED",
                    "require_rerun": False,
                    "reason": "Test reason",
                    "critique": "Test critique",
                    "market_alignment": "No market price data is available for this query.",
                }
            },
        }
    ]

    # Create the mock result
    mock_result = {
        "query_id": mock_query_id,
        "short_id": mock_short_id,
        "user_prompt": "Test prompt",
        "system_prompt": "Test system prompt",
        "router_result": {"solvers": ["perplexity"], "reason": "Test routing reason"},
        "solver_results": solver_results,
        "all_solver_results": solver_results,
        "overseer_result": {
            "decision": {
                "verdict": "SATISFIED",
                "require_rerun": False,
                "reason": "Test reason",
                "critique": "Test critique",
                "market_alignment": "No market price data is available for this query.",
            }
        },
        "recommendation": "p2",
        "reason": "Test reason",
        "market_alignment": "No market price data is available for this query.",
        "routing_attempts": 1,
        "attempted_solvers": ["perplexity"],
        "proposal_metadata": sample_proposal[0],
        "file_path": str(test_proposal_file),
    }

    return mock_result


def validate_fields(saved_result, sample_proposal, excluded_from_metadata=None):
    """Validate fields in the saved result."""
    if excluded_from_metadata is None:
        excluded_from_metadata = [
            "icon", "condition_id", "tags", "end_date_iso", "game_start_time",
            "proposed_price", "resolved_price", "resolved_price_outcome", "proposed_price_outcome"
        ]

    # Check for the format version first
    format_version = saved_result.get("format_version", 1)
    
    if format_version == 2:
        # For format version 2, check the new structure
        # Check for required top-level fields and sections
        top_level_required = [
            "query_id",
            "short_id",
            "question_id_short",
            "timestamp",
            "journey",
            "metadata",
            "market_data",
            "result",
            "proposal_metadata",
        ]

        missing_required = [
            field for field in top_level_required if field not in saved_result
        ]
        
        # Check required fields in sections
        if "result" in saved_result and "recommendation" not in saved_result["result"]:
            missing_required.append("recommendation (in result)")
        
        if "metadata" in saved_result and "processed_file" not in saved_result["metadata"]:
            missing_required.append("processed_file (in metadata)")
    else:
        # For format version 1, check the original structure
        top_level_required = [
            "query_id",
            "short_id",
            "question_id_short",
            "recommendation",
            "reason",
            "market_alignment",
            "timestamp",
            "processed_file",
        ]
        
        missing_required = [
            field for field in top_level_required if field not in saved_result
        ]

    if missing_required:
        print(f"❌ Missing required top-level fields: {missing_required}")
        return False
    else:
        print(f"✅ All required top-level fields present")

    # Check proposal_metadata
    if "proposal_metadata" not in saved_result:
        print("❌ Missing proposal_metadata in output")
        return False

    metadata = saved_result["proposal_metadata"]

    # Fields that should be in metadata and not excluded
    expected_metadata_fields = set(sample_proposal[0].keys())

    for field in excluded_from_metadata:
        if field in expected_metadata_fields:
            expected_metadata_fields.remove(field)

    missing_metadata_fields = [
        field for field in expected_metadata_fields if field not in metadata
    ]

    if missing_metadata_fields:
        print(
            f"❌ Missing expected fields in proposal_metadata: {missing_metadata_fields}"
        )
        return False
    else:
        print(f"✅ All expected fields present in proposal_metadata")

    # Check for fields that should not be duplicated
    format_version = saved_result.get("format_version", 1)
    
    if format_version == 2:
        # For format 2, check that fields are in their appropriate sections
        duplicated_fields_not_allowed = [
            # Fields that should only be in market_data
            {"field": "icon", "sections": ["market_data", "proposal_metadata"]},
            {"field": "condition_id", "sections": ["market_data", "proposal_metadata"]},
            {"field": "proposed_price", "sections": ["market_data", "proposal_metadata"]},
            # Fields that should only be in proposal_metadata
            {"field": "transaction_hash", "sections": ["proposal_metadata"]}
        ]
        
        duplicated_not_allowed = []
        
        for check in duplicated_fields_not_allowed:
            field = check["field"]
            sections = check["sections"]
            
            # Count how many sections have this field
            found_in = []
            for section in sections:
                if section in saved_result and field in saved_result[section]:
                    found_in.append(section)
                    
            # If field is in more than one section, it's duplicated
            if len(found_in) > 1:
                duplicated_not_allowed.append(f"{field} (in {', '.join(found_in)})")
    else:
        # For format 1, use the original duplication check
        duplicated_fields_not_allowed = ["icon", "condition_id", "transaction_hash"]
        duplicated_not_allowed = []

        for field in duplicated_fields_not_allowed:
            if field in saved_result and field in saved_result.get("proposal_metadata", {}):
                duplicated_not_allowed.append(field)

    if duplicated_not_allowed:
        print(f"❌ These fields should not be duplicated: {duplicated_not_allowed}")
        return False
    else:
        print(f"✅ No incorrect field duplication detected")

    # Validate with the validation function
    is_valid, missing_fields = validate_output_json(saved_result)
    if not is_valid:
        print(f"❌ Output JSON is missing required fields: {missing_fields}")
        return False
    else:
        print(f"✅ Output JSON passes validation function checks")

    return True


def main():
    """Main test function."""
    print("Starting multi_operator tests...")

    # Setup test directories
    test_output_dir, test_proposals_dir = setup_test_dirs()

    # Create test proposal
    test_proposal_file, sample_proposal = create_test_proposal(test_proposals_dir)

    # Create processor instance
    processor = MultiOperatorProcessor(
        proposals_dir=str(test_proposals_dir),
        output_dir=str(test_output_dir),
        verbose=True,
    )

    # Create mock result
    mock_result = create_mock_result(test_proposal_file, sample_proposal)

    # Save the result
    output_file = processor.save_result(mock_result)

    if not output_file:
        print("❌ Failed to save result")
        return 1

    print(f"✅ Successfully saved result to {output_file}")

    # Read the saved file to verify it contains all required fields
    with open(output_file, "r") as f:
        saved_result = json.load(f)

    # Validate fields
    if not validate_fields(saved_result, sample_proposal):
        return 1

    print("\n✅ All tests passed successfully!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
