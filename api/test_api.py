#!/usr/bin/env python3
"""
Test script for LLM Oracle API
"""

import httpx
import os
import sys
import json
from dotenv import load_dotenv
from pprint import pprint

# Load environment variables
load_dotenv()

# Configuration
API_BASE_URL = "http://localhost:8000"


def test_api_health():
    """Test API health endpoint"""
    url = f"{API_BASE_URL}/"

    try:
        response = httpx.get(url)
        print(f"Health check status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error testing API health: {e}")
        return False


def test_query_by_params(
    query_id=None, condition_id=None, transaction_hash=None, full=True
):
    """Test query by parameters endpoint"""
    url = f"{API_BASE_URL}/api/query"

    params = {}
    if query_id:
        params["query_id"] = query_id
    if condition_id:
        params["condition_id"] = condition_id
    if transaction_hash:
        params["transaction_hash"] = transaction_hash

    params["full"] = "true" if full else "false"

    try:
        response = httpx.get(url, params=params)
        print(f"\nQuery by params status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"Found {len(data)} results")

            if data:
                # Pretty print the first result
                print("First result:")
                pprint(data[0])

            return True
        else:
            print(f"Error: {response.text}")
            return False

    except Exception as e:
        print(f"Error querying API: {e}")
        return False


def test_get_by_experiment_id(experiment_id, full=True):
    """Test get by experiment ID endpoint"""
    url = f"{API_BASE_URL}/api/experiment/{experiment_id}"

    params = {"full": "true" if full else "false"}

    try:
        response = httpx.get(url, params=params)
        print(f"\nGet by experiment ID status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"Found {len(data)} results")

            if data:
                # Pretty print the first result
                print("First result:")
                pprint(data[0])

            return True
        else:
            print(f"Error: {response.text}")
            return False

    except Exception as e:
        print(f"Error querying API: {e}")
        return False


def test_get_by_question_id(question_id, full=True):
    """Test get by question ID endpoint"""
    url = f"{API_BASE_URL}/api/question/{question_id}"

    params = {"full": "true" if full else "false"}

    try:
        response = httpx.get(url, params=params)
        print(f"\nGet by question ID status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            # Pretty print the result
            print("Result:")
            pprint(data)
            return True
        else:
            print(f"Error: {response.text}")
            return False

    except Exception as e:
        print(f"Error querying API: {e}")
        return False


def test_advanced_query(
    identifier=None,
    start_timestamp=None,
    end_timestamp=None,
    ancillary_data=None,
    tags=None,
    recommendation=None,
    full=True,
):
    """Test advanced query endpoint"""
    url = f"{API_BASE_URL}/api/advanced-query"

    params = {}
    if identifier:
        params["identifier"] = identifier
    if start_timestamp:
        params["start_timestamp"] = start_timestamp
    if end_timestamp:
        params["end_timestamp"] = end_timestamp
    if ancillary_data:
        params["ancillary_data"] = ancillary_data
    if tags:
        # For multiple tags, add them as separate parameters with the same name
        for tag in tags:
            params.setdefault("tags", []).append(tag)
    if recommendation:
        params["recommendation"] = recommendation

    params["full"] = "true" if full else "false"

    try:
        response = httpx.get(url, params=params)
        print(f"\nAdvanced query status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"Found {len(data)} results")

            if data:
                # Pretty print the first result
                print("First result:")
                pprint(data[0])

            return True
        else:
            print(f"Error: {response.text}")
            return False

    except Exception as e:
        print(f"Error querying API: {e}")
        return False


def main():
    # Test health endpoint
    if not test_api_health():
        print("Health check failed. Make sure the API is running.")
        sys.exit(1)

    # Example values from the provided sample data
    example_query_id = (
        "0x21db972af5b6ac218f752a174751e0fb89164d2e574713d6162df5608afe87d2"
    )
    example_condition_id = (
        "0x8de5bc7b33f71bbe8414d4daa1308cc19893fcf0012f41532643a2eb03ed28f4"
    )
    example_transaction_hash = (
        "0xf2f4ebb8c3710d7476d18bc5b81ded2fdc4ff8f80a0005d75a7598994337d81d"
    )
    example_experiment_id = "08042025-multi-operator-with-realtime-bug-fix"
    example_question_id = "result_21db972a_20250408_125019"
    
    # Example values for advanced query
    example_timestamp_start = 1741964000
    example_timestamp_end = 1742148000
    example_ancillary_data = "Sample"
    example_tags = ["Crypto", "Bitcoin"]
    example_recommendation = "p1"
    example_identifier = "Bitcoin"

    # Test query by different parameters
    print("\n=== Testing query by query_id ===")
    test_query_by_params(query_id=example_query_id)

    print("\n=== Testing query by condition_id ===")
    test_query_by_params(condition_id=example_condition_id)

    print("\n=== Testing query by transaction_hash ===")
    test_query_by_params(transaction_hash=example_transaction_hash)

    print("\n=== Testing query by condition_id with reduced output ===")
    test_query_by_params(condition_id=example_condition_id, full=False)

    # Test advanced query
    print("\n=== Testing advanced query by timestamp range ===")
    test_advanced_query(
        start_timestamp=example_timestamp_start,
        end_timestamp=example_timestamp_end
    )

    print("\n=== Testing advanced query by identifier ===")
    test_advanced_query(identifier=example_identifier)

    print("\n=== Testing advanced query by ancillary data ===")
    test_advanced_query(ancillary_data=example_ancillary_data)

    print("\n=== Testing advanced query by tags ===")
    test_advanced_query(tags=example_tags)

    print("\n=== Testing advanced query by recommendation ===")
    test_advanced_query(recommendation=example_recommendation)

    # Test get by experiment ID
    print("\n=== Testing get by experiment ID ===")
    test_get_by_experiment_id(example_experiment_id)

    # Test get by question ID
    print("\n=== Testing get by question ID ===")
    test_get_by_question_id(example_question_id)

    print("\n=== Testing get by question ID with reduced output ===")
    test_get_by_question_id(example_question_id, full=False)


if __name__ == "__main__":
    main()
