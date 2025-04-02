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

# Add parent directory to path to allow importing the module
sys.path.insert(0, str(Path(__file__).parent.parent))

from multi_operator.proposal_processor import MultiOperatorProcessor
from multi_operator.common import get_question_id_short, validate_output_json


def main():
    # Create a test output directory
    test_output_dir = Path("test_output")
    if test_output_dir.exists():
        shutil.rmtree(test_output_dir)
    test_output_dir.mkdir(exist_ok=True)

    print(f"Testing proposal processing with output to {test_output_dir}")

    # Create a test proposals directory
    test_proposals_dir = Path("test_proposals")
    if test_proposals_dir.exists():
        shutil.rmtree(test_proposals_dir)
    test_proposals_dir.mkdir(exist_ok=True)

    # Create a sample proposal file based on 0a686fea.json
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

    test_proposal_file = test_proposals_dir / "questionId_e5373cc5.json"
    with open(test_proposal_file, "w") as f:
        json.dump(sample_proposal, f, indent=2)

    print(f"Created test proposal file: {test_proposal_file}")

    # Create a mock final result (simulating what would be produced by process_proposal)
    mock_query_id = "0xe5373cc54eb12bc20210bbc945d0eb96881c6bdd90057b67abe6958bcce77a9d"
    mock_short_id = get_question_id_short(mock_query_id)

    # Create a processor instance
    processor = MultiOperatorProcessor(
        proposals_dir=str(test_proposals_dir), output_dir=str(test_output_dir)
    )

    # Create solver_results and all_solver_results that are identical
    # to test that duplicates are removed
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

    # Create a mock result that simulates the output from process_proposal
    mock_result = {
        "query_id": mock_query_id,
        "short_id": mock_short_id,
        "user_prompt": "Test prompt",
        "system_prompt": "Test system prompt",
        "router_result": {"solvers": ["perplexity"], "reason": "Test routing reason"},
        "solver_results": solver_results,
        "all_solver_results": solver_results,  # Intentionally duplicate solver_results
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
        "proposal_metadata": sample_proposal[0],  # Using the full proposal object
        "file_path": str(test_proposal_file),
    }

    # Save the result
    output_file = processor.save_result(mock_result)

    if output_file:
        print(f"✅ Successfully saved result to {output_file}")

        # Read the saved file to verify it contains all required fields
        with open(output_file, "r") as f:
            saved_result = json.load(f)

        # Import the validation function and use it
        is_valid, missing_fields = validate_output_json(saved_result)

        if is_valid:
            print(f"✅ Output JSON is valid for backward compatibility")
        else:
            print(
                f"❌ Output JSON is missing required fields for backward compatibility:"
            )
            for field in missing_fields:
                print(f"  - {field}")

        # Check for required top-level fields
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
        else:
            print(f"✅ All required top-level fields present")

        # Ensure proposal_metadata exists and contains all fields from the original proposal
        if "proposal_metadata" not in saved_result:
            print("❌ Missing proposal_metadata in output")
        else:
            metadata = saved_result["proposal_metadata"]

            # Fields that should be in metadata and not excluded
            expected_metadata_fields = set(sample_proposal[0].keys())
            # Fields that we intentionally move from metadata to top-level only
            excluded_from_metadata = ["icon", "condition_id"]

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
            else:
                print(f"✅ All expected fields present in proposal_metadata")

            # Check for specific important fields in proposal_metadata
            metadata_required = [
                "transaction_hash",  # Should be in metadata only
                "tags",  # Shared field
                "disputer_address",  # Metadata only
                "proposed_price",  # Shared field
                "resolved_price",  # Shared field
            ]

            # Remove fields that should not be in metadata
            for field in excluded_from_metadata:
                if field in metadata_required:
                    metadata_required.remove(field)

            missing_metadata_required = [
                field for field in metadata_required if field not in metadata
            ]
            if missing_metadata_required:
                print(
                    f"❌ Missing important fields in proposal_metadata: {missing_metadata_required}"
                )
            else:
                print(f"✅ All important fields present in proposal_metadata")

        # Check for fields that should not be duplicated
        # We now expect certain fields to be duplicated for backward compatibility
        duplicated_fields_not_allowed = ["icon", "condition_id", "transaction_hash"]
        duplicated_not_allowed = []

        for field in duplicated_fields_not_allowed:
            if field in saved_result and field in saved_result.get(
                "proposal_metadata", {}
            ):
                duplicated_not_allowed.append(field)

        if duplicated_not_allowed:
            print(f"❌ These fields should not be duplicated: {duplicated_not_allowed}")
        else:
            print(f"✅ No incorrect field duplication detected")

        # Check for shared fields (expected to be at both levels)
        shared_fields = [
            "proposed_price",
            "resolved_price",
            "proposed_price_outcome",
            "resolved_price_outcome",
            "tags",
            "end_date_iso",
            "game_start_time",
        ]

        missing_shared = []
        for field in shared_fields:
            if field not in saved_result or field not in saved_result.get(
                "proposal_metadata", {}
            ):
                missing_shared.append(field)

        if missing_shared:
            print(f"❌ These fields should appear at both levels: {missing_shared}")
        else:
            print(f"✅ All shared fields correctly appear at both levels")

        # Check if all_solver_results was removed since it was identical to solver_results
        if "all_solver_results" in saved_result:
            print(
                "❌ Found all_solver_results which should have been removed (duplicate of solver_results)"
            )
        else:
            print("✅ Properly removed duplicate all_solver_results")

        # Print all top-level fields for verification
        print("\nTop-level fields in output JSON:")
        for field in sorted(saved_result.keys()):
            if field not in [
                "solver_results",
                "overseer_result",
                "proposal_metadata",
                "router_result",
            ]:
                value = saved_result[field]
                # Truncate long values for display
                if isinstance(value, str) and len(value) > 50:
                    value = value[:47] + "..."
                print(f"  - {field}: {value}")
    else:
        print("❌ Failed to save result")


if __name__ == "__main__":
    main()
