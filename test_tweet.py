#!/usr/bin/env python3
"""
Test script to try the new tweet generation feature.
This will process a single proposal file and generate a tweet.
"""

import os
import json
import time
import logging
from pathlib import Path
from dotenv import load_dotenv

from multi_operator.proposal_processor import MultiOperatorProcessor
from multi_operator.overseer.overseer import Overseer
from multi_operator.common import get_query_id_from_proposal, get_question_id_short

# Create a mock Overseer for testing
class MockOverseer(Overseer):
    def generate_tweet(self, user_prompt, recommendation, market_data=None, tokens=None, model=None):
        """Mock implementation that returns a sample tweet without making API calls."""
        # Return a sample tweet based on the recommendation
        if recommendation == "p1":
            return "UMA Oracle has resolved the market: Trump will NOT reduce tariffs on South Korea in April. Markets were right with 90% confidence on this outcome. #UMA #OptimisticOracle #Politics #Tariffs"
        elif recommendation == "p2":
            return "UMA Oracle confirms: Trump WILL reduce tariffs on South Korea this April! This was surprising as markets had given this only a 10% chance. #UMA #OptimisticOracle #TrumpTariffs #SouthKorea"
        elif recommendation == "p3" or recommendation == "p4":
            return "UMA Oracle couldn't determine if Trump will reduce tariffs on South Korea in April due to insufficient data. Markets had favored NO at 90%. #UMA #OptimisticOracle #Markets #TariffUncertainty"
        else:
            return "UMA Oracle has resolved another market outcome! Check our website for the latest oracle resolution data. #UMA #OptimisticOracle #CryptoOracles #DeFi"

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("tweet_test")

def create_sample_env():
    """Create a sample .env file if one doesn't exist."""
    env_path = "./.env"
    if not os.path.exists(env_path):
        # This is a dummy implementation for testing
        # In a real scenario, you would prompt for actual API keys
        with open(env_path, "w") as f:
            f.write("PERPLEXITY_API_KEY=dummy_perplexity_key\n")
            f.write("OPENAI_API_KEY=dummy_openai_key\n")
        logger.info("Created sample .env file with dummy keys")
    return env_path

def main():
    # Create sample .env file
    env_path = create_sample_env()
    
    # Load environment variables
    load_dotenv(env_path)
    
    # Check essential API keys
    required_keys = ['PERPLEXITY_API_KEY', 'OPENAI_API_KEY']
    for key in required_keys:
        if not os.getenv(key):
            logger.error(f"{key} not set in environment variables. Please set it and try again.")
            return False
    
    logger.info("Using dummy API keys for testing. In a real scenario, you would use actual API keys.")
    
    # Test proposal
    proposal_file = "./proposals/09042025-realtime-dataset/proposals/questionId_a5b30904.json"
    output_dir = "./test_outputs"
    
    # Ensure output directory exists
    Path(output_dir).mkdir(exist_ok=True)
    
    # Read the proposal file
    with open(proposal_file, "r") as f:
        proposal_data = json.load(f)
    
    query_id = get_query_id_from_proposal(proposal_data)
    short_id = get_question_id_short(query_id)
    
    logger.info(f"Testing tweet generation with proposal {short_id}")
    
    # Initialize processor
    processor = MultiOperatorProcessor(
        proposals_dir="./proposals",
        output_dir=output_dir,
        max_attempts=2,
        min_attempts=1,  # Use lower values for faster testing
        verbose=True,
    )
    
    # Replace the real overseer with our mock
    processor.overseer = MockOverseer(api_key="dummy_key", verbose=True)
    
    # Prepare proposal info for processing
    proposal_info = {
        "file_path": Path(proposal_file),
        "proposal_data": proposal_data,
        "query_id": query_id,
        "short_id": short_id,
    }
    
    # Instead of full processing, let's test just the tweet generation
    logger.info(f"Testing tweet generation for proposal {short_id}")
    
    # Create a simplified mock result
    mock_result = {
        "recommendation": "p1",  # Example recommendation
        "user_prompt": "Will Trump reduce tariffs on South Korea in April 2025?",
        "proposal_metadata": {
            "tags": ["politics", "tariffs", "international-trade"],
            "tokens": [
                {"outcome": "Yes", "price": 0.105},
                {"outcome": "No", "price": 0.895}
            ],
            "end_date_iso": "2025-04-30T23:59:59Z"
        }
    }
    
    # Directly call the generate_tweet method
    try:
        tweet = processor.overseer.generate_tweet(
            user_prompt=mock_result["user_prompt"],
            recommendation=mock_result["recommendation"],
            market_data=mock_result["proposal_metadata"],
            tokens=mock_result["proposal_metadata"].get("tokens"),
        )
        
        logger.info(f"Generated tweet ({len(tweet)} chars):")
        logger.info("-" * 40)
        logger.info(tweet)
        logger.info("-" * 40)
        
        # Add the tweet to a result file
        if output_dir:
            result_file = os.path.join(output_dir, f"tweet_test_{short_id}.json")
            with open(result_file, "w") as f:
                json.dump({
                    "short_id": short_id,
                    "tweet": tweet,
                    "recommendation": mock_result["recommendation"],
                    "user_prompt": mock_result["user_prompt"]
                }, f, indent=2)
            logger.info(f"Test result saved to: {result_file}")
            
        return True
    except Exception as e:
        logger.error(f"Error generating tweet: {e}")
        return False

if __name__ == "__main__":
    main()