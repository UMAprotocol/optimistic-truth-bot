#!/usr/bin/env python3
"""
Script to fetch market resolution data for a specific UMA Optimistic Oracle market ID. This utility connects to the Polygon blockchain and retrieves detailed information
about a market resolution, including question data, resolution status, and price.

Example:
    python query_utilities/fetch_market_resolution.py 0x0FC5D2B61B29D54D487ACBC27E9694CEF303A9891433925E282742B1DBA4F399
"""

from web3 import Web3
from dotenv import load_dotenv
import os
import sys
import requests
import time

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import (
    load_abi,
    OptimisticOracleV2,
    UmaCtfAdapter,
    NegRiskUmaCtfAdapter,
    yesOrNoIdentifier,
    compute_condition_id,
    get_polymarket_data,
)


def main(question_id):
    print(f"Starting fetch for question ID: {question_id}")

    # Load environment and setup Web3
    load_dotenv()
    w3 = Web3(Web3.HTTPProvider(os.getenv("POLYGON_RPC_URL")))
    print(f"Connected to chain: {w3.is_connected()}")

    # Setup contract instances
    adapter_contract = w3.eth.contract(
        address=UmaCtfAdapter, abi=load_abi("UmaCtfAdapter.json")
    )
    oov2_contract = w3.eth.contract(
        address=OptimisticOracleV2, abi=load_abi("OptimisticOracleV2.json")
    )

    # Query adapter for question data
    question_data = adapter_contract.functions.questions(question_id).call()
    print("\nQuestion Details:")
    print("----------------------------------------")
    print(f"Request Timestamp:              {question_data[0]}")
    print(f"Reward Amount:                  {question_data[1]}")
    print(f"Proposal Bond:                  {question_data[2]}")
    print(f"Emergency Resolution Timestamp: {question_data[3]}")
    print(f"Resolved:                       {question_data[4]}")
    print(f"Paused:                         {question_data[5]}")
    print(f"Reset:                          {question_data[6]}")
    print(f"Reward Token:                   {question_data[7]}")
    print(f"Creator:                        {question_data[8]}")
    print(f"Ancillary Data:                 {question_data[9]}")
    print("----------------------------------------")

    # Extract needed data and query OOV2
    timestamp = question_data[0]  # requestTimestamp
    creator = question_data[8]  # creator (requester)
    ancillary_data = question_data[9]  # keep as raw bytes from web3

    request_data = oov2_contract.functions.getRequest(
        UmaCtfAdapter, yesOrNoIdentifier, timestamp, "0x" + ancillary_data.hex()
    ).call()

    print("\nRequest Details from OOV2:")
    print("----------------------------------------")
    print(f"Proposer:                      {request_data[0]}")
    print(f"Disputer:                      {request_data[1]}")
    print(f"Currency:                      {request_data[2]}")
    print(f"Settled:                       {request_data[3]}")
    print(f"Event Based:                   {request_data[4][0]}")
    print(f"Refund On Dispute:             {request_data[4][1]}")
    print(f"Callback On Price Proposed:    {request_data[4][2]}")
    print(f"Callback On Price Disputed:    {request_data[4][3]}")
    print(f"Callback On Price Settled:     {request_data[4][4]}")
    print(f"Bond:                          {request_data[4][5]}")
    print(f"Custom Liveness:               {request_data[4][6]}")
    print(f"Proposed Price:                {request_data[5]}")
    print(f"Resolved Price:                {request_data[6]}")
    print(f"Expiration Time:               {request_data[7]}")
    print(f"Reward:                        {request_data[8]}")
    print(f"Final Fee:                     {request_data[9]}")
    print("----------------------------------------")

    # Get Polymarket data
    print("\nPolymarket Information:")
    print("----------------------------------------")
    condition_id = compute_condition_id(UmaCtfAdapter, question_id, 2)
    print(f"Condition ID:                  {condition_id}")
    
    condition_id_alternative = compute_condition_id(NegRiskUmaCtfAdapter, question_id, 1)
    print(f"Condition ID Alternative:      {condition_id_alternative}")

    poly_data = get_polymarket_data(condition_id)
    if poly_data:
        tags = poly_data.get("tags", [])
        print(f"Tags:                          {tags}")
        print(
            f"End Date:                      {poly_data.get('end_date_iso', 'Not available')}"
        )
        print(
            f"Game Start Time:               {poly_data.get('game_start_time', 'Not available')}"
        )
    else:
        print("No Polymarket data available for this condition ID")
    print("----------------------------------------")

    # Check if market has settled
    if not request_data[3]:  # settled flag
        print("\nMarket Status: Not settled yet")
    else:
        print("\nMarket Status: Settled")
        # Get resolved price and decode from 1e18 scaling
        resolved_price = request_data[6] / 1e18

        # Interpret resolution based on standard values
        if resolved_price == 0:
            print("Resolution: NO (p1)")
        elif resolved_price == 1:
            print("Resolution: YES (p2)")
        elif resolved_price == 0.5:
            print("Resolution: UNKNOWN/CANNOT BE DETERMINED (p3)")
        elif (
            resolved_price
            == -57896044618658097711785492504343953926634992332820282019728.792003956564819968
        ):
            print("Resolution: WAITING FOR MORE INFO (p4)")
        else:
            print(f"Resolution: Non-standard value: {resolved_price}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python fetch_market_resolution.py <question_id>")
        sys.exit(1)

    question_id = sys.argv[1]
    # Validate and format hex string
    if question_id.startswith("0x"):
        # Validate hex string length and format
        if len(question_id) != 66:  # '0x' + 64 hex chars
            print("Error: Hex question ID must be 32 bytes (64 characters) long")
            sys.exit(1)
        try:
            int(question_id, 16)  # Validate hex format
        except ValueError:
            print("Error: Invalid hex format")
            sys.exit(1)
    else:
        try:
            question_id = int(question_id)
        except ValueError:
            print(
                "Error: Question ID must be either a hex string starting with '0x' or a valid integer"
            )
            sys.exit(1)

    main(question_id)
