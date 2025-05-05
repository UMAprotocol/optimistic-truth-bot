#!/usr/bin/env python3
"""
Tests for the Twitter client
"""

import unittest
import sys
import os
from unittest.mock import patch, MagicMock, call

# Add parent directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from twitter_client import create_twitter_client, MockTwitterClient


class TestTwitterClient(unittest.TestCase):
    """Test the Twitter client functionality"""

    def test_mock_client(self):
        """Test the mock Twitter client"""
        # Create a mock client
        config = {
            "twitter_test_mode": True
        }
        client = create_twitter_client(config)
        
        # Verify it's a MockTwitterClient
        self.assertIsInstance(client, MockTwitterClient)
        
        # Test posting a tweet
        result = client.post_tweet("Test tweet")
        self.assertTrue(result)
        
        # Verify the tweet was recorded
        self.assertEqual(len(client.tweets), 1)
        self.assertEqual(client.tweets[0]["text"], "Test tweet")
        
        # Test with media
        result = client.post_tweet("Test with media", media_paths=["test.jpg"])
        self.assertTrue(result)
        self.assertEqual(len(client.tweets), 2)
        self.assertEqual(client.tweets[1]["media_paths"], ["test.jpg"])
        
        # Test get_user_info
        user_info = client.get_user_info()
        self.assertEqual(user_info["screen_name"], "mock_oracle")
        self.assertEqual(user_info["statuses_count"], 2)

    @patch('twitter_client.TweepyClient')
    def test_client_factory_tweepy(self, mock_tweepy_client):
        """Test client factory with Tweepy credentials"""
        # Mock tweepy module
        sys.modules['tweepy'] = MagicMock()
        
        # Create config with Tweepy credentials
        config = {
            "twitter_api_key": "test_key",
            "twitter_api_secret": "test_secret",
            "twitter_access_token": "test_token",
            "twitter_access_token_secret": "test_token_secret"
        }
        
        # Mock tweepy client instance
        mock_instance = MagicMock()
        mock_tweepy_client.return_value = mock_instance
        
        # Create client
        client = create_twitter_client(config)
        
        # Verify TweepyClient was created
        mock_tweepy_client.assert_called_once_with(config)
        
        # Clean up
        del sys.modules['tweepy']

    @patch('twitter_client.TwitterAPIv2Client')
    def test_client_factory_v2(self, mock_v2_client):
        """Test client factory with Twitter API v2 credentials"""
        # Mock twitter module
        sys.modules['twitter'] = MagicMock()
        sys.modules['twitter.account'] = MagicMock()
        
        # Create config with v2 credentials
        config = {
            "twitter_bearer_token": "test_bearer_token"
        }
        
        # Mock v2 client instance
        mock_instance = MagicMock()
        mock_v2_client.return_value = mock_instance
        
        # Create client
        client = create_twitter_client(config)
        
        # Verify TwitterAPIv2Client was created
        mock_v2_client.assert_called_once_with(config)
        
        # Clean up
        del sys.modules['twitter']
        del sys.modules['twitter.account']

    def test_client_factory_fallback(self):
        """Test client factory fallback to mock client"""
        # Create config without credentials
        config = {}
        
        # Create client
        client = create_twitter_client(config)
        
        # Verify it's a MockTwitterClient
        self.assertIsInstance(client, MockTwitterClient)


if __name__ == '__main__':
    unittest.main()