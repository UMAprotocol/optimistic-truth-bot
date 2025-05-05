#!/usr/bin/env python3
"""
Main entry point for the LLM Oracle Tweet Generator.

This script sets up and runs the tweet generator with the specified configuration.
"""

import os
import sys
import argparse
import logging
from pathlib import Path

# Add parent directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import tweet generator modules
from tweet_generator.config import load_config, validate_config, add_config_arguments, update_config_from_args
from tweet_generator.logging_setup import setup_logging, add_sentry_logging
from tweet_generator.oracle_api_client import OracleApiClient
from tweet_generator.tweet_content import TweetContentGenerator
from tweet_generator.twitter_client import create_twitter_client
from tweet_generator.scheduler import ScheduleManager


def main():
    """Main entry point"""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="LLM Oracle Tweet Generator")
    parser = add_config_arguments(parser)
    args = parser.parse_args()
    
    try:
        # Load configuration
        config = load_config(args.config)
        config = update_config_from_args(config, args)
        config = validate_config(config)
        
        # Set up logging
        logger = setup_logging(config)
        
        # Add Sentry error tracking if configured
        if config.get("sentry_dsn"):
            add_sentry_logging(config, logger)
        
        # Log configuration (excluding sensitive values)
        logger.info("Tweet generator starting with configuration:")
        for key, value in config.items():
            if key in ["twitter_api_key", "twitter_api_secret", "twitter_access_token", 
                      "twitter_access_token_secret", "twitter_bearer_token", "sentry_dsn"]:
                if value:
                    logger.info(f"  {key}: [REDACTED]")
                else:
                    logger.info(f"  {key}: [NOT SET]")
            else:
                logger.info(f"  {key}: {value}")
        
        # Create API client
        api_client = OracleApiClient(base_url=config.get("oracle_api_url"))
        
        # Check API health
        try:
            health = api_client.get_health()
            logger.info(f"API health: {health}")
        except Exception as e:
            logger.error(f"API health check failed: {e}")
            return 1
        
        # Create tweet generator
        tweet_generator = TweetContentGenerator(
            max_length=config.get("max_tweet_length", 280),
            include_hashtags=config.get("include_hashtags", True),
            include_links=config.get("include_links", True)
        )
        
        # Create Twitter client
        twitter_client = create_twitter_client(config)
        
        # Create scheduler
        scheduler = ScheduleManager(
            state_file=config.get("state_file", "tweet_state.json"),
            check_interval=config.get("check_interval", 300),
            tweet_cooldown=config.get("tweet_cooldown", 3600),
            max_tweets_per_day=config.get("max_tweets_per_day", 48),
            results_lookback_hours=config.get("results_lookback_hours", 24)
        )
        
        # Start the scheduler
        logger.info("Starting tweet generator")
        try:
            scheduler.start(api_client, tweet_generator, twitter_client.post_tweet)
        except KeyboardInterrupt:
            logger.info("Interrupted by user")
        finally:
            scheduler.stop()
            logger.info("Tweet generator stopped")
        
        return 0
        
    except Exception as e:
        logging.critical(f"Error starting tweet generator: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())