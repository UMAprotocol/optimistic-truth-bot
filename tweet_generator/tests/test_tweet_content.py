#!/usr/bin/env python3
"""
Tests for the tweet content generator
"""

import unittest
import sys
import os
from unittest.mock import patch, MagicMock

# Add parent directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from tweet_content import TweetContentGenerator


class TestTweetContentGenerator(unittest.TestCase):
    """Test the TweetContentGenerator class"""

    def setUp(self):
        """Set up test fixtures"""
        self.generator = TweetContentGenerator(max_length=280, include_hashtags=True, include_links=True)

        # Create a sample result for testing
        self.sample_result = {
            "query_id": "0x024e024afcbaf99e7d295f5017eea2398c6bc718e56063abfea70cdc5ed43934",
            "short_id": "024e024a",
            "recommendation": "p2",
            "tags": ["Crypto", "Ethereum", "eth", "Crypto Prices", "2025 Predictions"],
            "proposal_metadata": {
                "ancillary_data": "q: title: Will Ethereum dip to $1,500 by December 31?, description: This market will immediately resolve to \"Yes\" if any Binance 1 minute candle for Ethereum (ETHUSDT) between December 30, 2024, 21:00 and December 31, 2025, 23:59 in the ET timezone has a final \"Low\" price of $1,500.00 or lower. Otherwise, this market will resolve to \"No.\""
            }
        }

    def test_extract_title(self):
        """Test extracting title from result data"""
        title = self.generator._extract_title(self.sample_result)
        self.assertEqual(title, "Will Ethereum dip to $1,500 by December 31?")

    def test_extract_title_missing(self):
        """Test extracting title when it's missing"""
        result = {
            "query_id": "test_id",
            "short_id": "test_short",
            "proposal_metadata": {
                "ancillary_data": "No title here"
            }
        }
        title = self.generator._extract_title(result)
        self.assertEqual(title, "Prediction test_short")

    def test_get_recommendation_text(self):
        """Test getting recommendation text"""
        texts = {
            "p1": "No",
            "p2": "Yes",
            "p3": "Uncertain",
            "p4": "Cannot be determined yet",
            "unknown": "Unknown"
        }

        for code, expected in texts.items():
            result = {"recommendation": code}
            self.assertEqual(self.generator._get_recommendation_text(result), expected)

    def test_generate_hashtags(self):
        """Test generating hashtags from tags"""
        hashtags = self.generator._generate_hashtags(self.sample_result)
        self.assertIn("#Crypto", hashtags)
        self.assertIn("#Ethereum", hashtags)
        self.assertIn("#eth", hashtags)
        self.assertIn("#LLMOracle", hashtags)

    def test_generate_tweet(self):
        """Test generating a complete tweet"""
        with patch.object(self.generator, "_generate_link", return_value="http://example.com/q/123"):
            tweet = self.generator.generate_tweet(self.sample_result)
            self.assertIn("Will Ethereum dip to $1,500 by December 31?", tweet)
            self.assertIn("Yes", tweet)
            self.assertIn("#Crypto", tweet)
            self.assertIn("http://example.com", tweet)
            self.assertLessEqual(len(tweet), 280)

    def test_generate_batch(self):
        """Test generating a batch of tweets"""
        with patch.object(self.generator, "_generate_link", return_value="http://example.com/q/123"):
            batch = self.generator.generate_batch([self.sample_result] * 3, max_tweets=2)
            self.assertEqual(len(batch), 2)
            for tweet in batch:
                self.assertIn("Will Ethereum dip to $1,500 by December 31?", tweet)

    def test_tweet_length_limit(self):
        """Test that tweets are limited to max_length"""
        # Create a result with a very long title
        long_result = dict(self.sample_result)
        long_result["proposal_metadata"] = {
            "ancillary_data": "q: title: " + "X" * 300 + ", description: Test"
        }

        # Set a short max length to force truncation
        generator = TweetContentGenerator(max_length=100, include_hashtags=True, include_links=True)
        with patch.object(generator, "_generate_link", return_value="http://example.com/q/123"):
            tweet = generator.generate_tweet(long_result)
            self.assertLessEqual(len(tweet), 100)
            self.assertTrue(tweet.endswith("..."))

    def test_sanitize_tweet(self):
        """Test sanitizing tweet text"""
        # Test HTML entity decoding
        self.assertEqual(self.generator._sanitize_tweet("&lt;test&gt;"), "<test>")
        
        # Test length limiting
        self.assertEqual(self.generator._sanitize_tweet("x" * 300), "x" * 277 + "...")


if __name__ == '__main__':
    unittest.main()