#!/usr/bin/env python3
"""
Twitter Client for the LLM Oracle Tweet Generator

This module provides functionality to post tweets to Twitter using their API.
It supports both Twitter API v1.1 with Tweepy and Twitter API v2 with the official client.
"""

import os
import sys
import time
import logging
from typing import Dict, List, Any, Optional
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Define a base TwitterClientError
class TwitterClientError(Exception):
    """Base exception for Twitter client errors"""
    pass

class TwitterClient:
    """
    Base Twitter client class
    
    This is an abstract base class for Twitter clients.
    Actual implementations should extend this class.
    """
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Twitter client
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.logger = logging.getLogger("twitter_client")
        self.is_configured = False
        
    def post_tweet(self, text: str, media_paths: Optional[List[str]] = None) -> bool:
        """
        Post a tweet
        
        Args:
            text: Tweet text
            media_paths: List of paths to media files to attach
            
        Returns:
            True if successful, False otherwise
            
        Raises:
            NotImplementedError: This is an abstract method
        """
        raise NotImplementedError("Subclasses must implement post_tweet")
        
    def get_user_info(self) -> Dict[str, Any]:
        """
        Get information about the authenticated user
        
        Returns:
            Dictionary with user information
            
        Raises:
            NotImplementedError: This is an abstract method
        """
        raise NotImplementedError("Subclasses must implement get_user_info")


class TweepyClient(TwitterClient):
    """
    Twitter client using Tweepy (Twitter API v1.1)
    """
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Tweepy client
        
        Args:
            config: Configuration dictionary
        """
        super().__init__(config)
        self.api = None
        self._initialize_client()
        
    def _initialize_client(self):
        """Initialize the Tweepy client"""
        try:
            # Import tweepy here to avoid making it a required dependency
            import tweepy
            
            # Get API credentials from config
            api_key = self.config.get("twitter_api_key")
            api_secret = self.config.get("twitter_api_secret")
            access_token = self.config.get("twitter_access_token")
            access_token_secret = self.config.get("twitter_access_token_secret")
            
            # Check if all required credentials are present
            if not all([api_key, api_secret, access_token, access_token_secret]):
                self.logger.warning("Twitter API credentials are incomplete. Tweeting will be disabled.")
                self.is_configured = False
                return
                
            # Set up authentication
            auth = tweepy.OAuth1UserHandler(
                api_key, api_secret, access_token, access_token_secret
            )
            
            # Create API instance
            self.api = tweepy.API(auth)
            
            # Test the credentials
            self.api.verify_credentials()
            
            self.is_configured = True
            self.logger.info("Tweepy client initialized successfully")
            
        except ImportError:
            self.logger.error("Tweepy is not installed. Please install it with 'pip install tweepy'")
            self.is_configured = False
        except Exception as e:
            self.logger.error(f"Error initializing Tweepy client: {e}")
            self.is_configured = False
            
    def post_tweet(self, text: str, media_paths: Optional[List[str]] = None) -> bool:
        """
        Post a tweet using Tweepy
        
        Args:
            text: Tweet text
            media_paths: List of paths to media files to attach
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_configured or not self.api:
            self.logger.warning("Tweepy client is not properly configured")
            return False
            
        try:
            # Handle media uploads if provided
            media_ids = []
            if media_paths:
                for media_path in media_paths:
                    if os.path.exists(media_path):
                        media = self.api.media_upload(media_path)
                        media_ids.append(media.media_id)
                    else:
                        self.logger.warning(f"Media file not found: {media_path}")
            
            # Post the tweet
            if media_ids:
                self.api.update_status(text, media_ids=media_ids)
            else:
                self.api.update_status(text)
                
            self.logger.info("Tweet posted successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error posting tweet: {e}")
            return False
            
    def get_user_info(self) -> Dict[str, Any]:
        """
        Get information about the authenticated user
        
        Returns:
            Dictionary with user information
        """
        if not self.is_configured or not self.api:
            self.logger.warning("Tweepy client is not properly configured")
            return {}
            
        try:
            user = self.api.verify_credentials()
            return {
                "id": user.id_str,
                "screen_name": user.screen_name,
                "name": user.name,
                "description": user.description,
                "followers_count": user.followers_count,
                "friends_count": user.friends_count,
                "statuses_count": user.statuses_count
            }
        except Exception as e:
            self.logger.error(f"Error getting user info: {e}")
            return {}


class TwitterAPIv2Client(TwitterClient):
    """
    Twitter client using the official Twitter API v2 client
    """
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Twitter API v2 client
        
        Args:
            config: Configuration dictionary
        """
        super().__init__(config)
        self.client = None
        self._initialize_client()
        
    def _initialize_client(self):
        """Initialize the Twitter API v2 client"""
        try:
            # Import the Twitter API client here to avoid making it a required dependency
            from twitter.account import UserAccount
            
            # Get API credentials from config
            bearer_token = self.config.get("twitter_bearer_token")
            
            # Check if the required credential is present
            if not bearer_token:
                self.logger.warning("Twitter API v2 bearer token is missing. Tweeting will be disabled.")
                self.is_configured = False
                return
                
            # Create client instance
            self.client = UserAccount(bearer_token=bearer_token)
            
            # Test the credentials by getting user info
            self.client.get_me()
            
            self.is_configured = True
            self.logger.info("Twitter API v2 client initialized successfully")
            
        except ImportError:
            self.logger.error("Twitter API v2 client is not installed. Please install it with 'pip install twitter-api-client'")
            self.is_configured = False
        except Exception as e:
            self.logger.error(f"Error initializing Twitter API v2 client: {e}")
            self.is_configured = False
    
    def post_tweet(self, text: str, media_paths: Optional[List[str]] = None) -> bool:
        """
        Post a tweet using Twitter API v2
        
        Args:
            text: Tweet text
            media_paths: List of paths to media files to attach
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_configured or not self.client:
            self.logger.warning("Twitter API v2 client is not properly configured")
            return False
            
        try:
            # Handle media uploads if provided
            media_ids = []
            if media_paths:
                for media_path in media_paths:
                    if os.path.exists(media_path):
                        # Upload media and get the media ID
                        media_upload_result = self.client.media.upload_media(media_path=media_path)
                        media_ids.append(media_upload_result.get("media_id_string"))
                    else:
                        self.logger.warning(f"Media file not found: {media_path}")
            
            # Prepare the tweet payload
            payload = {"text": text}
            if media_ids:
                payload["media"] = {"media_ids": media_ids}
                
            # Post the tweet
            response = self.client.tweet.create_tweet(**payload)
            
            self.logger.info(f"Tweet posted successfully with ID: {response.get('data', {}).get('id')}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error posting tweet: {e}")
            return False
            
    def get_user_info(self) -> Dict[str, Any]:
        """
        Get information about the authenticated user
        
        Returns:
            Dictionary with user information
        """
        if not self.is_configured or not self.client:
            self.logger.warning("Twitter API v2 client is not properly configured")
            return {}
            
        try:
            user_data = self.client.get_me(user_fields=["description", "public_metrics"])
            user = user_data.get("data", {})
            
            return {
                "id": user.get("id"),
                "screen_name": user.get("username"),
                "name": user.get("name"),
                "description": user.get("description"),
                "followers_count": user.get("public_metrics", {}).get("followers_count"),
                "friends_count": user.get("public_metrics", {}).get("following_count"),
                "statuses_count": user.get("public_metrics", {}).get("tweet_count")
            }
        except Exception as e:
            self.logger.error(f"Error getting user info: {e}")
            return {}


class MockTwitterClient(TwitterClient):
    """
    Mock Twitter client for testing/development
    
    This client doesn't actually post tweets, but logs them for inspection.
    """
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the mock Twitter client
        
        Args:
            config: Configuration dictionary
        """
        super().__init__(config)
        self.is_configured = True
        self.tweets = []
        self.logger.info("Mock Twitter client initialized")
        
    def post_tweet(self, text: str, media_paths: Optional[List[str]] = None) -> bool:
        """
        Mock posting a tweet
        
        Args:
            text: Tweet text
            media_paths: List of paths to media files to attach
            
        Returns:
            Always returns True
        """
        tweet_data = {
            "text": text,
            "media_paths": media_paths,
            "timestamp": time.time()
        }
        
        self.tweets.append(tweet_data)
        self.logger.info(f"MOCK TWEET: {text}")
        
        if media_paths:
            self.logger.info(f"With media: {media_paths}")
        
        return True
        
    def get_user_info(self) -> Dict[str, Any]:
        """
        Get mock user information
        
        Returns:
            Dictionary with mock user information
        """
        return {
            "id": "12345678",
            "screen_name": "mock_oracle",
            "name": "LLM Oracle (Mock)",
            "description": "This is a mock Twitter client for testing",
            "followers_count": 1000,
            "friends_count": 100,
            "statuses_count": len(self.tweets)
        }
        
    def get_tweets(self) -> List[Dict[str, Any]]:
        """
        Get all tweets posted with this mock client
        
        Returns:
            List of tweet data dictionaries
        """
        return self.tweets


class DemoTwitterClient(TwitterClient):
    """
    Demo Twitter client for development/preview
    
    This client uses real data but instead of posting to Twitter,
    it logs the tweets to the console in a formatted way.
    """
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the demo Twitter client
        
        Args:
            config: Configuration dictionary
        """
        super().__init__(config)
        self.is_configured = True
        self.tweets = []
        self.logger.info("Demo Twitter client initialized")
        
    def post_tweet(self, text: str, media_paths: Optional[List[str]] = None) -> bool:
        """
        Demo posting a tweet - logs to console but doesn't actually post
        
        Args:
            text: Tweet text
            media_paths: List of paths to media files to attach
            
        Returns:
            Always returns True
        """
        tweet_data = {
            "text": text,
            "media_paths": media_paths,
            "timestamp": time.time()
        }
        
        self.tweets.append(tweet_data)
        
        # Log the tweet in a formatted way
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        border = "=" * 60
        
        print(f"\n{border}")
        print(f" DEMO TWEET - {timestamp}")
        print(f"{border}")
        print(f"\n{text}\n")
        
        if media_paths:
            print(f"Media attachments: {', '.join(media_paths)}")
        
        print(f"{border}\n")
        
        self.logger.info(f"Demo tweet created (not actually posted): {text}")
        
        return True
        
    def get_user_info(self) -> Dict[str, Any]:
        """
        Get demo user information
        
        Returns:
            Dictionary with demo user information
        """
        return {
            "id": "demo-user",
            "screen_name": "llm_oracle_demo",
            "name": "LLM Oracle (Demo)",
            "description": "This is a demo Twitter client for development",
            "followers_count": 0,
            "friends_count": 0,
            "statuses_count": len(self.tweets)
        }
        
    def get_tweets(self) -> List[Dict[str, Any]]:
        """
        Get all tweets created with this demo client
        
        Returns:
            List of tweet data dictionaries
        """
        return self.tweets


def create_twitter_client(config: Dict[str, Any]) -> TwitterClient:
    """
    Create a Twitter client based on the available credentials and libraries
    
    Args:
        config: Configuration dictionary
        
    Returns:
        TwitterClient instance
    """
    logger = logging.getLogger("twitter_client_factory")
    
    # Check if we're in demo mode
    if config.get("twitter_demo_mode", False):
        logger.info("Using demo Twitter client")
        return DemoTwitterClient(config)
    
    # Check if we're in test mode
    if config.get("twitter_test_mode", False):
        logger.info("Using mock Twitter client")
        return MockTwitterClient(config)
    
    # Try to create a Tweepy client first
    if all([
        config.get("twitter_api_key"),
        config.get("twitter_api_secret"),
        config.get("twitter_access_token"),
        config.get("twitter_access_token_secret")
    ]):
        try:
            import tweepy
            logger.info("Using Tweepy client")
            return TweepyClient(config)
        except ImportError:
            logger.warning("Tweepy is not installed, falling back to v2 client")
    
    # Try to create a Twitter API v2 client
    if config.get("twitter_bearer_token"):
        try:
            from twitter.account import UserAccount
            logger.info("Using Twitter API v2 client")
            return TwitterAPIv2Client(config)
        except ImportError:
            logger.warning("Twitter API v2 client is not installed, falling back to demo client")
    
    # Fall back to demo client if no clients could be created
    logger.warning("No Twitter client could be created, using demo client")
    return DemoTwitterClient(config)


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Example configuration
    config = {
        "twitter_demo_mode": True,  # Use demo client
        "twitter_api_key": os.getenv("TWITTER_API_KEY", ""),
        "twitter_api_secret": os.getenv("TWITTER_API_SECRET", ""),
        "twitter_access_token": os.getenv("TWITTER_ACCESS_TOKEN", ""),
        "twitter_access_token_secret": os.getenv("TWITTER_ACCESS_TOKEN_SECRET", ""),
        "twitter_bearer_token": os.getenv("TWITTER_BEARER_TOKEN", "")
    }
    
    # Create a Twitter client
    client = create_twitter_client(config)
    
    # Get user info
    user_info = client.get_user_info()
    print(f"User info: {json.dumps(user_info, indent=2)}")
    
    # Post a test tweet
    success = client.post_tweet("This is a test tweet from the LLM Oracle Tweet Generator!")
    print(f"Tweet posted: {success}")
    
    # If using the demo or mock client, print all tweets
    if isinstance(client, (MockTwitterClient, DemoTwitterClient)):
        print(f"History: {json.dumps(client.get_tweets(), indent=2)}")