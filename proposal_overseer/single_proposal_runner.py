#!/usr/bin/env python3
"""
UMA Single Proposal Runner - Run one specific proposal with Perplexity-ChatGPT validation loop
Usage: python proposal_overseer/single_proposal_runner.py --question-id QUESTION_ID_SHORT [--proposals-dir PATH] [--output-dir PATH]
"""

import os
import json
import time
import sys
import argparse
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import re
import logging

# Parse command line arguments
parser = argparse.ArgumentParser(
    description="UMA Single Proposal Runner with ChatGPT Oversight"
)
parser.add_argument(
    "--question-id",
    type=str,
    required=True,
    help="Short question ID to process (e.g. '12345678')",
)
parser.add_argument(
    "--proposals-dir",
    type=str,
    help="Directory containing proposal JSON files",
)
parser.add_argument(
    "--output-dir",
    type=str,
    help="Directory to store output files. If not specified, results will only be logged without saving files.",
)
parser.add_argument(
    "--max-attempts",
    type=int,
    default=3,
    help="Maximum number of attempts to query Perplexity with ChatGPT validation",
)
parser.add_argument(
    "--min-attempts",
    type=int,
    default=2,
    help="Minimum number of attempts before defaulting to p4",
)
parser.add_argument(
    "--verbose",
    action="store_true",
    help="Enable verbose output with detailed logs",
)
args = parser.parse_args()

print(
    f"🔍 UMA Single Proposal Runner - Processing proposal for question ID: {args.question_id} 🤖"
)

# Import locally defined modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from prompt import get_system_prompt
from proposal_overseer.common import (
    setup_logging,
    extract_recommendation,
    query_perplexity,
    query_chatgpt,
    extract_prompt_update,
    get_overseer_decision,
    enhanced_perplexity_chatgpt_loop,
    get_token_price,
)
from proposal_overseer.prompt_overseer import format_market_price_info

# Setup logging
logger = setup_logging("single_proposal_runner", "logs/single_proposal_runner.log")
load_dotenv()
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Verify API keys are available
if not PERPLEXITY_API_KEY:
    logger.error("PERPLEXITY_API_KEY not found in environment variables")
    sys.exit(1)

if not OPENAI_API_KEY:
    logger.error("OPENAI_API_KEY not found in environment variables")
    sys.exit(1)

# Set the proposals directory - use command line argument if provided, otherwise use default
PROPOSALS_DIR = (
    Path(args.proposals_dir)
    if args.proposals_dir
    else Path(__file__).parent / "proposals"
)

# Determine if output should be saved
SAVE_OUTPUT = args.output_dir is not None
OUTPUTS_DIR = None

# Set up output directory if saving is enabled
if SAVE_OUTPUT:
    OUTPUTS_DIR = Path(args.output_dir)
    OUTPUTS_DIR.mkdir(exist_ok=True)
    logger.info(f"Output will be saved to: {OUTPUTS_DIR}")
else:
    logger.info(
        "No output directory specified - results will only be logged (not saved to files)"
    )
    print(
        "No output directory specified - results will only be logged (not saved to files)"
    )

# Ensure proposals directory exists
if not PROPOSALS_DIR.exists():
    logger.error(f"Proposals directory not found: {PROPOSALS_DIR}")
    sys.exit(1)

# Store args values
QUESTION_ID_SHORT = args.question_id
MAX_ATTEMPTS = args.max_attempts
MIN_ATTEMPTS = args.min_attempts
VERBOSE = args.verbose

# Log configuration
logger.info(f"Looking for proposal with question_id_short: {QUESTION_ID_SHORT}")
logger.info(f"Proposals directory set to: {PROPOSALS_DIR}")
logger.info(f"Maximum attempts set to: {MAX_ATTEMPTS}")
logger.info(f"Minimum attempts before defaulting to p4: {MIN_ATTEMPTS}")
logger.info(f"Verbose logging: {'Enabled' if VERBOSE else 'Disabled'}")


def format_prompt_from_json(proposal_data):
    """Format a user prompt from the proposal data JSON."""
    if isinstance(proposal_data, list) and len(proposal_data) > 0:
        proposal_data = proposal_data[0]

    ancillary_data = proposal_data.get("ancillary_data", "")
    resolution_conditions = proposal_data.get("resolution_conditions", "")
    updates = proposal_data.get("updates", [])

    prompt = f"user:\n\nancillary_data:\n{ancillary_data}\n\n"
    if resolution_conditions:
        prompt += f"resolution_conditions:\n{resolution_conditions}\n\n"
    if updates:
        prompt += f"updates:\n{updates}"
    return prompt


def get_query_id_from_proposal(proposal_data):
    """Extract the query ID from a proposal."""
    if isinstance(proposal_data, list) and len(proposal_data) > 0:
        return proposal_data[0].get("query_id", "")
    return proposal_data.get("query_id", "")


def get_question_id_short(query_id):
    """Get the short question ID from a full query ID."""
    if not query_id:
        return "unknown"
    return query_id[2:10] if query_id.startswith("0x") else query_id[:8]


def find_proposal_file_by_short_id(short_id):
    """Find a proposal file by its short question ID."""
    for file_path in PROPOSALS_DIR.glob("*.json"):
        try:
            with open(file_path, "r") as f:
                proposal_data = json.load(f)

            query_id = get_query_id_from_proposal(proposal_data)
            current_short_id = get_question_id_short(query_id)

            if current_short_id == short_id:
                logger.info(f"Found matching proposal file: {file_path}")
                return file_path
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")

    return None


def process_single_proposal(file_path):
    """Process a single proposal file with detailed logging of all steps."""
    file_name = os.path.basename(file_path)
    process_start_time = time.time()

    logger.info(f"Processing proposal file: {file_name}")
    print(f"Processing proposal file: {file_name}")

    try:
        # Open and parse the proposal file
        with open(file_path, "r") as f:
            proposal_data = json.load(f)

        # Extract query ID and prepare prompt
        query_id = get_query_id_from_proposal(proposal_data)
        short_id = get_question_id_short(query_id)

        logger.info(f"Full query ID: {query_id}")
        print(f"Full query ID: {query_id}")

        # Extract token information if available
        tokens = None
        market_price_info = None
        is_list = isinstance(proposal_data, list) and len(proposal_data) > 0
        proposal_obj = proposal_data[0] if is_list else proposal_data

        if "tokens" in proposal_obj:
            tokens = proposal_obj.get("tokens", [])
            logger.info(f"Found {len(tokens)} tokens in proposal data")
            print(f"Found {len(tokens)} tokens in proposal data")

            # Update token prices from Polymarket API
            for token in tokens:
                token_id = token.get("token_id")
                if token_id:
                    logger.info(f"Fetching price for token {token_id}")
                    print(f"Fetching price for token {token_id}")
                    price_data = get_token_price(token_id)
                    if price_data and "price" in price_data:
                        # Update the token price with the latest data
                        token["price"] = price_data["price"]
                        logger.info(
                            f"Updated token {token_id} price to {price_data['price']}"
                        )
                        print(
                            f"Updated token {token_id} price to {price_data['price']}"
                        )

            # Format market price information for ChatGPT
            market_price_info = format_market_price_info(tokens)
            logger.info(f"Prepared market price info for ChatGPT overseer")
            if VERBOSE:
                print(f"Prepared market price info for ChatGPT overseer")
                print("\n" + "=" * 80)
                print("MARKET PRICE INFORMATION:")
                print(market_price_info)
                print("=" * 80 + "\n")

        # Setup inputs for API calls
        user_prompt = format_prompt_from_json(proposal_data)
        system_prompt = get_system_prompt()

        # Log the prompts
        if VERBOSE:
            print("\n" + "=" * 80)
            print("SYSTEM PROMPT:")
            print(system_prompt)
            print("=" * 80)
            print("\nUSER PROMPT:")
            print(user_prompt)
            print("=" * 80 + "\n")

        logger.info("System prompt and user prompt prepared")

        # Extract transaction hash and proposed price
        tx_hash = (proposal_data[0] if is_list else proposal_data).get(
            "transaction_hash", ""
        )
        price = (proposal_data[0] if is_list else proposal_data).get(
            "proposed_price", None
        )

        # Run the enhanced Perplexity-ChatGPT loop
        logger.info(f"Starting Perplexity-ChatGPT loop for {short_id}")
        print(f"Starting Perplexity-ChatGPT loop for {short_id}")

        start_time = time.time()

        # Make API calls
        result = enhanced_perplexity_chatgpt_loop(
            user_prompt=user_prompt,
            perplexity_api_key=PERPLEXITY_API_KEY,
            chatgpt_api_key=OPENAI_API_KEY,
            original_system_prompt=system_prompt,
            logger=logger,
            max_attempts=MAX_ATTEMPTS,
            min_attempts=MIN_ATTEMPTS,
            verbose=VERBOSE,
            market_price_info=market_price_info,
        )

        api_time = time.time() - start_time
        logger.info(f"API calls completed in {api_time:.2f} seconds")
        print(f"API calls completed in {api_time:.2f} seconds")

        # Verify we have valid responses
        perplexity_responses = [
            r
            for r in result.get("responses", [])
            if r.get("interaction_type") == "perplexity_query"
        ]

        if not perplexity_responses:
            error_msg = f"No valid Perplexity responses for {short_id}"
            logger.error(error_msg)
            print(f"ERROR: {error_msg}")
            return False

        # Extract and organize proposal metadata
        if isinstance(proposal_data, list) and len(proposal_data) > 0:
            raw_data = proposal_data[0]
        else:
            raw_data = proposal_data

        proposal_metadata = {
            "creator": raw_data.get("creator", ""),
            "proposal_bond": raw_data.get("proposal_bond", 0),
            "reward_amount": raw_data.get("reward_amount", 0),
            "unix_timestamp": raw_data.get("unix_timestamp", 0),
            "block_number": raw_data.get("block_number", 0),
            "updates": raw_data.get("updates", []),
            "ancillary_data_hex": raw_data.get("ancillary_data_hex", ""),
        }

        # Prepare output data
        final_response = next(
            (
                r
                for r in reversed(result["responses"])
                if r.get("interaction_type") == "perplexity_query"
            ),
            None,
        )

        output_data = {
            "query_id": query_id,
            "question_id_short": short_id,
            "transaction_hash": tx_hash,
            "proposed_price": price,
            "resolved_price": None,
            "timestamp": time.time(),
            "processed_file": file_name,
            "proposal_metadata": proposal_metadata,
            "resolved_price_outcome": None,
            "disputed": False,
            "recommendation": result["final_recommendation"],
            "recommendation_overridden": result.get("recommendation_overridden", False),
            "proposed_price_outcome": extract_recommendation(result["final_response"]),
            "user_prompt": user_prompt,
            "system_prompt": system_prompt,
            "overseer_data": {
                "attempts": result["attempts"],
                "interactions": result["responses"],
                "market_price_info": market_price_info,  # Include market price info in output
                "tokens": tokens,  # Include token data in output
                "recommendation_journey": [
                    {
                        "attempt": i + 1,
                        "perplexity_recommendation": next(
                            (
                                r["recommendation"]
                                for r in result["responses"]
                                if r.get("attempt") == i + 1
                                and r["interaction_type"] == "perplexity_query"
                            ),
                            None,
                        ),
                        "overseer_satisfaction_level": next(
                            (
                                r.get("satisfaction_level")
                                for r in result["responses"]
                                if r.get("stage") == f"evaluation_{i+1}"
                                and r["interaction_type"] == "chatgpt_evaluation"
                            ),
                            None,
                        ),
                        "prompt_updated": next(
                            (
                                r.get("prompt_updated", False)
                                for r in result["responses"]
                                if r.get("stage") == f"evaluation_{i+1}"
                                and r["interaction_type"] == "chatgpt_evaluation"
                            ),
                            False,
                        ),
                        "critique": next(
                            (
                                r.get("critique", "")
                                for r in result["responses"]
                                if r.get("stage") == f"evaluation_{i+1}"
                                and r["interaction_type"] == "chatgpt_evaluation"
                            ),
                            None,
                        ),
                        "system_prompt_before": next(
                            (
                                r.get("system_prompt_before", "")
                                for r in result["responses"]
                                if r.get("stage") == f"evaluation_{i+1}"
                                and r["interaction_type"] == "chatgpt_evaluation"
                            ),
                            "",
                        ),
                        "system_prompt_after": next(
                            (
                                r.get("system_prompt_after", "")
                                for r in result["responses"]
                                if r.get("stage") == f"evaluation_{i+1}"
                                and r["interaction_type"] == "chatgpt_evaluation"
                            ),
                            "",
                        ),
                    }
                    for i in range(result["attempts"])
                ],
                "final_response_metadata": (
                    final_response.get("response_metadata")
                    if final_response and final_response.get("response_metadata")
                    else None
                ),
            },
        }

        # Include tags if they exist
        if "tags" in raw_data:
            output_data["tags"] = raw_data.get("tags", [])

        # Save output if output directory is specified
        if SAVE_OUTPUT:
            output_file = OUTPUTS_DIR / f"{short_id}.json"
            with open(output_file, "w") as f:
                json.dump(output_data, f, indent=2)
            logger.info(f"Output saved to {output_file}")
            print(f"Output saved to {output_file}")
        else:
            logger.info(f"Output not saved (no output directory specified)")
            print(f"Output not saved (no output directory specified)")

        total_time = time.time() - process_start_time

        print("\n" + "=" * 80)
        print(f"SUMMARY FOR {short_id}:")
        print(f"- Final recommendation: {output_data['recommendation']}")
        print(f"- Attempts: {result['attempts']}/{MAX_ATTEMPTS}")
        print(
            f"- Recommendation changed: {result.get('recommendation_changed', False)}"
        )
        print(
            f"- Recommendation overridden: {result.get('recommendation_overridden', False)}"
        )
        print(f"- Processing time: {total_time:.2f} seconds")

        # Print market price summary if available
        if market_price_info:
            print(f"- Market price data: Found for {len(tokens)} tokens")
            yes_token = next(
                (t for t in tokens if t.get("outcome", "").upper() == "YES"), None
            )
            no_token = next(
                (t for t in tokens if t.get("outcome", "").upper() == "NO"), None
            )
            if yes_token:
                print(f"  YES token price: {yes_token.get('price', 'Unknown')}")
            if no_token:
                print(f"  NO token price: {no_token.get('price', 'Unknown')}")
        else:
            print("- Market price data: None available")

        print("=" * 80 + "\n")

        # Print all interactions if verbose mode is enabled
        if VERBOSE:
            print("\nDETAILED INTERACTION LOG:")
            for i, interaction in enumerate(result["responses"]):
                interaction_type = interaction.get("interaction_type", "unknown")
                if interaction_type == "perplexity_query":
                    attempt = interaction.get("attempt", "?")
                    recommendation = interaction.get("recommendation", "unknown")
                    print(
                        f"\nPerplexity Query (Attempt {attempt}) - Recommendation: {recommendation}"
                    )
                    print("-" * 40)
                    print(interaction.get("response", "No response content"))
                    print("-" * 40)
                elif interaction_type == "chatgpt_evaluation":
                    stage = interaction.get("stage", "unknown")
                    satisfaction = interaction.get("satisfaction_level", "unknown")
                    print(
                        f"\nChatGPT Evaluation ({stage}) - Satisfaction: {satisfaction}"
                    )
                    print("-" * 40)
                    print(interaction.get("response", "No response content"))
                    print("-" * 40)

        return True

    except Exception as e:
        logger.error(f"Error processing proposal: {str(e)}")
        print(f"ERROR: {str(e)}")
        return False


def main():
    logger.info(f"Starting single proposal runner for question ID: {QUESTION_ID_SHORT}")

    # Find the proposal file by short ID
    proposal_file = find_proposal_file_by_short_id(QUESTION_ID_SHORT)

    if not proposal_file:
        logger.error(f"No proposal file found for question ID: {QUESTION_ID_SHORT}")
        print(f"ERROR: No proposal file found for question ID: {QUESTION_ID_SHORT}")
        sys.exit(1)

    # Process the proposal
    success = process_single_proposal(proposal_file)

    if success:
        logger.info("Single proposal processing completed successfully")
        print("Single proposal processing completed successfully")
    else:
        logger.error("Single proposal processing failed")
        print("Single proposal processing failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
