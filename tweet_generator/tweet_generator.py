#!/usr/bin/env python3
"""
LLM Oracle Tweet Generator

This script fetches data from the LLM Oracle API and generates tweets about the latest results.
It can be run on a schedule to regularly post updates about new Oracle predictions and outcomes.
"""

import os
import sys
import json
import time
import logging
import argparse
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import requests
from dotenv import load_dotenv

# Add parent directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from common import setup_logging

# Load environment variables
load_dotenv()

class OracleApiClient:
    """
    Client for interacting with the LLM Oracle API
    """
    def __init__(self, base_url: str = None):
        """
        Initialize the API client
        
        Args:
            base_url: Base URL for the API. If None, uses the environment variable or default
        """
        self.base_url = base_url or os.getenv("ORACLE_API_URL", "https://api.llo.uma.xyz")
        self.logger = logging.getLogger("oracle_api_client")
    
    def get_health(self) -> Dict[str, Any]:
        """Check API health"""
        response = requests.get(f"{self.base_url}/")
        response.raise_for_status()
        return response.json()
    
    def query_recent_results(self, 
                            hours: int = 24, 
                            limit: int = 20, 
                            recommendation: Optional[str] = None, 
                            tags: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Query recent results from the API
        
        Args:
            hours: Number of hours to look back
            limit: Maximum number of results to return
            recommendation: Filter by recommendation (p1, p2, p3, p4)
            tags: Filter by tags
            
        Returns:
            List of recent results
        """
        # Calculate timestamps
        end_timestamp = int(time.time())
        start_timestamp = end_timestamp - (hours * 3600)
        
        # Build query parameters
        params = {
            "start_timestamp": start_timestamp,
            "end_timestamp": end_timestamp,
            "limit": limit,
            "full": "true"
        }
        
        if recommendation:
            params["recommendation"] = recommendation
            
        if tags:
            params["tags"] = tags
            
        self.logger.info(f"Querying API for results since {datetime.fromtimestamp(start_timestamp)}")
        
        # Make the API request
        try:
            response = requests.get(f"{self.base_url}/api/advanced-query", params=params)
            response.raise_for_status()
            results = response.json()
            self.logger.info(f"Found {len(results)} results")
            return results
        except requests.RequestException as e:
            self.logger.error(f"API request failed: {e}")
            return []

    def get_experiment_results(self, experiment_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get results for a specific experiment
        
        Args:
            experiment_id: ID of the experiment
            limit: Maximum number of results to return
            
        Returns:
            List of experiment results
        """
        try:
            response = requests.get(
                f"{self.base_url}/api/experiment/{experiment_id}",
                params={"limit": limit, "full": "true"}
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            self.logger.error(f"Failed to get experiment results: {e}")
            return []
            
    def get_question_result(self, question_id: str) -> Optional[Dict[str, Any]]:
        """
        Get result for a specific question
        
        Args:
            question_id: ID of the question
            
        Returns:
            Question result or None if not found
        """
        try:
            response = requests.get(
                f"{self.base_url}/api/question/{question_id}",
                params={"full": "true"}
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            self.logger.error(f"Failed to get question result: {e}")
            return None


class TweetGenerator:
    """
    Generates tweet content based on Oracle results
    """
    def __init__(self, api_client: OracleApiClient):
        """
        Initialize the tweet generator
        
        Args:
            api_client: Oracle API client
        """
        self.api_client = api_client
        self.logger = logging.getLogger("tweet_generator")
        
    def generate_tweet_for_result(self, result: Dict[str, Any]) -> str:
        """
        Generate a tweet for a specific result
        
        Args:
            result: Oracle result data
            
        Returns:
            Tweet text
        """
        # Extract relevant information from the result
        title = self._extract_title(result)
        recommendation = result.get("recommendation", "unknown")
        outcome_mapping = {
            "p1": "No",
            "p2": "Yes",
            "p3": "Uncertain",
            "p4": "Cannot be determined yet"
        }
        outcome = outcome_mapping.get(recommendation, "Unknown")
        
        # Get the tags
        tags = result.get("tags", [])
        hashtags = " ".join([f"#{tag.replace(' ', '')}" for tag in tags if tag])
        
        # Create the tweet text
        tweet = f"LLM Oracle predicts: {title} - {outcome}"
        
        # Add the tags if they exist and there's room
        if hashtags and len(tweet) + len(hashtags) + 1 <= 280:
            tweet = f"{tweet}\n{hashtags}"
            
        # Add a link to the UI if available and there's room
        ui_url = os.getenv("ORACLE_UI_URL")
        if ui_url and result.get("question_id"):
            short_id = result.get("short_id") or result.get("question_id_short")
            if short_id:
                link = f"{ui_url}/question/{short_id}"
                if len(tweet) + len(link) + 1 <= 280:
                    tweet = f"{tweet}\n{link}"
        
        return tweet
    
    def _extract_title(self, result: Dict[str, Any]) -> str:
        """
        Extract the title from the result data
        
        Args:
            result: Oracle result data
            
        Returns:
            Title or a placeholder if not found
        """
        # Try to get the title from ancillary_data
        ancillary_data = result.get("proposal_metadata", {}).get("ancillary_data", "")
        
        # Look for title in the ancillary data
        title_start = ancillary_data.find("title:")
        if title_start != -1:
            title_start += 6  # Length of "title:"
            title_end = ancillary_data.find(",", title_start)
            if title_end == -1:
                title_end = ancillary_data.find("\n", title_start)
            
            if title_end != -1:
                title = ancillary_data[title_start:title_end].strip()
                return title
        
        # If we couldn't extract the title, return a placeholder with the question ID
        question_id = result.get("question_id", "")
        short_id = result.get("short_id") or result.get("question_id_short", "")
        return f"Prediction {short_id or question_id}"

    def generate_recent_tweets(self, hours: int = 24, limit: int = 5) -> List[str]:
        """
        Generate tweets for recent results
        
        Args:
            hours: Hours to look back
            limit: Maximum number of tweets to generate
            
        Returns:
            List of tweet texts
        """
        results = self.api_client.query_recent_results(hours=hours, limit=limit)
        tweets = []
        
        for result in results:
            try:
                tweet = self.generate_tweet_for_result(result)
                tweets.append(tweet)
                self.logger.info(f"Generated tweet: {tweet}")
            except Exception as e:
                self.logger.error(f"Failed to generate tweet for result: {e}")
                
        return tweets


class TwitterClient:
    """
    Client for posting to Twitter
    
    Note: This is a placeholder implementation.
    You will need to integrate with a Twitter API library like tweepy.
    """
    def __init__(self):
        """Initialize the Twitter client"""
        self.logger = logging.getLogger("twitter_client")
        # Here you would initialize the Twitter API client with your credentials
        # For example, if using tweepy:
        # self.api = tweepy.API(auth)
        self.is_configured = False
        self._check_configuration()
        
    def _check_configuration(self):
        """Check if Twitter API is configured"""
        # Placeholder for checking API configuration
        # For example:
        api_key = os.getenv("TWITTER_API_KEY")
        api_secret = os.getenv("TWITTER_API_SECRET")
        access_token = os.getenv("TWITTER_ACCESS_TOKEN")
        access_token_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
        
        self.is_configured = all([api_key, api_secret, access_token, access_token_secret])
        
        if not self.is_configured:
            self.logger.warning("Twitter API not fully configured. Tweets will be logged but not posted.")
    
    def post_tweet(self, tweet_text: str) -> bool:
        """
        Post a tweet
        
        Args:
            tweet_text: The text to tweet
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_configured:
            self.logger.info(f"Would have tweeted (API not configured): {tweet_text}")
            return False
            
        try:
            # Here you would call the Twitter API to post the tweet
            # For example with tweepy:
            # self.api.update_status(tweet_text)
            
            # For now, we'll just log it
            self.logger.info(f"Tweeted: {tweet_text}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to post tweet: {e}")
            return False


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="LLM Oracle Tweet Generator")
    parser.add_argument("--hours", type=int, default=24, help="Hours to look back for results")
    parser.add_argument("--limit", type=int, default=5, help="Maximum number of tweets to generate")
    parser.add_argument("--post", action="store_true", help="Actually post tweets (otherwise just log them)")
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], default="INFO", help="Logging level")
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(level=args.log_level, log_to_console=True)
    logger = logging.getLogger("tweet_generator_main")
    
    # Create API client
    api_client = OracleApiClient()
    
    # Check API health
    try:
        health = api_client.get_health()
        logger.info(f"API health: {health}")
    except Exception as e:
        logger.error(f"API health check failed: {e}")
        return 1
    
    # Create tweet generator
    generator = TweetGenerator(api_client)
    
    # Generate tweets
    tweets = generator.generate_recent_tweets(hours=args.hours, limit=args.limit)
    
    # Post tweets if requested
    if args.post and tweets:
        twitter = TwitterClient()
        for tweet in tweets:
            success = twitter.post_tweet(tweet)
            if success:
                logger.info("Tweet posted successfully")
            else:
                logger.warning("Tweet was not posted")
    elif tweets:
        logger.info(f"Generated {len(tweets)} tweets (use --post to actually post them)")
        for i, tweet in enumerate(tweets, 1):
            logger.info(f"Tweet {i}: {tweet}")
    else:
        logger.info("No tweets generated")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())