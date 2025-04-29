#!/usr/bin/env python3
"""
Standalone test script for the tweet generation feature.
This doesn't depend on any other code in the repository.
"""

import os
import json
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("tweet_test")

def generate_tweet(user_prompt, recommendation, market_data=None):
    """Mock tweet generation that returns a sample tweet."""
    # Return a sample tweet based on the recommendation
    if recommendation == "p1":
        return "UMA Oracle has resolved the market: Trump will NOT reduce tariffs on South Korea in April. Markets were right with 90% confidence on this outcome. #UMA #OptimisticOracle #Politics #Tariffs"
    elif recommendation == "p2":
        return "UMA Oracle confirms: Trump WILL reduce tariffs on South Korea this April! This was surprising as markets had given this only a 10% chance. #UMA #OptimisticOracle #TrumpTariffs #SouthKorea"
    elif recommendation == "p3" or recommendation == "p4":
        return "UMA Oracle couldn't determine if Trump will reduce tariffs on South Korea in April due to insufficient data. Markets had favored NO at 90%. #UMA #OptimisticOracle #Markets #TariffUncertainty"
    else:
        return "UMA Oracle has resolved another market outcome! Check our website for the latest oracle resolution data. #UMA #OptimisticOracle #CryptoOracles #DeFi"

def main():
    """Test the tweet generation feature with mock data."""
    # Test output directory
    output_dir = "./test_outputs"
    Path(output_dir).mkdir(exist_ok=True)
    
    # Sample market data
    market_data = {
        "short_id": "a5b30904",
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
    
    logger.info(f"Testing tweet generation for market: {market_data['user_prompt']}")
    
    # Generate tweet
    tweet = generate_tweet(
        user_prompt=market_data["user_prompt"],
        recommendation=market_data["recommendation"],
        market_data=market_data["proposal_metadata"],
    )
    
    logger.info(f"Generated tweet ({len(tweet)} chars):")
    logger.info("-" * 40)
    logger.info(tweet)
    logger.info("-" * 40)
    
    # Save the result
    result_file = os.path.join(output_dir, f"tweet_test_{market_data['short_id']}.json")
    with open(result_file, "w") as f:
        json.dump({
            "short_id": market_data["short_id"],
            "tweet": tweet,
            "recommendation": market_data["recommendation"],
            "user_prompt": market_data["user_prompt"]
        }, f, indent=2)
    
    logger.info(f"Test result saved to: {result_file}")
    
    # Try different recommendations
    for rec in ["p2", "p3", "p4"]:
        alt_tweet = generate_tweet(
            user_prompt=market_data["user_prompt"],
            recommendation=rec,
            market_data=market_data["proposal_metadata"],
        )
        logger.info(f"Alternative tweet for {rec} ({len(alt_tweet)} chars):")
        logger.info("-" * 40)
        logger.info(alt_tweet)
        logger.info("-" * 40)
    
    return True

if __name__ == "__main__":
    main()