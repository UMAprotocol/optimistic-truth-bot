#!/usr/bin/env python3
"""
Tweet Content Generator

This module generates tweet content based on Oracle results.
"""

import os
import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import html

class TweetContentGenerator:
    """
    Generates tweet content based on Oracle results
    """
    def __init__(self, max_length: int = 280, include_hashtags: bool = True, include_links: bool = True):
        """
        Initialize the tweet content generator
        
        Args:
            max_length: Maximum tweet length
            include_hashtags: Whether to include hashtags
            include_links: Whether to include links
        """
        self.max_length = max_length
        self.include_hashtags = include_hashtags
        self.include_links = include_links
        self.logger = logging.getLogger("tweet_content_generator")
        self.ui_url = os.getenv("ORACLE_UI_URL", "")
        
    def generate_tweet(self, result: Dict[str, Any]) -> str:
        """
        Generate a tweet for a result
        
        Args:
            result: Oracle result data
            
        Returns:
            Tweet text
        """
        # Get the basic components
        title = self._extract_title(result)
        recommendation = self._get_recommendation_text(result)
        hashtags = self._generate_hashtags(result) if self.include_hashtags else ""
        link = self._generate_link(result) if self.include_links else ""
        
        # Start with the core content
        tweet = f"LLM Oracle predicts: {title} - {recommendation}"
        
        # Add additional components if they fit
        components = []
        remaining_length = self.max_length - len(tweet)
        
        # Add hashtags if there's room
        if hashtags and remaining_length > len(hashtags) + 1:
            components.append(hashtags)
            remaining_length -= len(hashtags) + 1
        
        # Add link if there's room
        if link and remaining_length > len(link) + 1:
            components.append(link)
        
        # Combine everything
        if components:
            tweet = f"{tweet}\n{'\n'.join(components)}"
        
        return self._sanitize_tweet(tweet)
        
    def generate_batch(self, results: List[Dict[str, Any]], max_tweets: int = 10) -> List[str]:
        """
        Generate tweets for a batch of results
        
        Args:
            results: List of Oracle results
            max_tweets: Maximum number of tweets to generate
            
        Returns:
            List of tweet texts
        """
        tweets = []
        
        for result in results[:max_tweets]:
            try:
                tweet = self.generate_tweet(result)
                tweets.append(tweet)
                self.logger.debug(f"Generated tweet: {tweet}")
            except Exception as e:
                self.logger.error(f"Failed to generate tweet for result: {e}")
                
        return tweets
    
    def generate_outcome_summary(self, results: List[Dict[str, Any]]) -> str:
        """
        Generate a summary tweet for multiple outcomes
        
        Args:
            results: List of Oracle results
            
        Returns:
            Summary tweet text
        """
        if not results:
            return "No recent LLM Oracle predictions to report."
            
        # Count recommendation types
        outcomes = {"p1": 0, "p2": 0, "p3": 0, "p4": 0}
        for result in results:
            recommendation = result.get("recommendation")
            if recommendation in outcomes:
                outcomes[recommendation] += 1
        
        # Create a readable summary
        outcome_mapping = {
            "p1": "No",
            "p2": "Yes",
            "p3": "Uncertain",
            "p4": "Cannot determine yet"
        }
        
        summary_parts = []
        for outcome, count in outcomes.items():
            if count > 0:
                summary_parts.append(f"{outcome_mapping[outcome]}: {count}")
                
        summary = "LLM Oracle predictions today: " + ", ".join(summary_parts)
        
        # Add hashtags if there's room
        if self.include_hashtags:
            hashtags = "#LLMOracle #Prediction #Polymarket"
            if len(summary) + len(hashtags) + 1 <= self.max_length:
                summary = f"{summary}\n{hashtags}"
        
        return self._sanitize_tweet(summary)
    
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
                # Truncate if too long
                if len(title) > 100:
                    title = title[:97] + "..."
                return title
        
        # If we couldn't extract the title, return a placeholder with the question ID
        question_id = result.get("question_id", "")
        short_id = result.get("short_id") or result.get("question_id_short", "")
        return f"Prediction {short_id or question_id}"
    
    def _get_recommendation_text(self, result: Dict[str, Any]) -> str:
        """
        Get the recommendation text
        
        Args:
            result: Oracle result data
            
        Returns:
            Recommendation text
        """
        recommendation = result.get("recommendation", "unknown")
        outcome_mapping = {
            "p1": "No",
            "p2": "Yes",
            "p3": "Uncertain",
            "p4": "Cannot be determined yet"
        }
        return outcome_mapping.get(recommendation, "Unknown")
    
    def _generate_hashtags(self, result: Dict[str, Any]) -> str:
        """
        Generate hashtags from tags
        
        Args:
            result: Oracle result data
            
        Returns:
            Hashtags string
        """
        # Get tags from the result
        tags = result.get("tags", [])
        if not tags:
            tags = result.get("proposal_metadata", {}).get("tags", [])
            
        if not tags:
            return "#LLMOracle #Prediction"
            
        # Process tags into hashtags
        hashtags = []
        for tag in tags:
            if tag:
                # Remove spaces and special characters
                hashtag = "#" + re.sub(r'[^\w]', '', tag)
                hashtags.append(hashtag)
                
        # Add generic hashtags
        hashtags.extend(["#LLMOracle", "#Prediction"])
        
        # Deduplicate and join
        return " ".join(sorted(set(hashtags)))
    
    def _generate_link(self, result: Dict[str, Any]) -> str:
        """
        Generate a link to the result
        
        Args:
            result: Oracle result data
            
        Returns:
            Link string or empty string if not available
        """
        if not self.ui_url:
            return ""
            
        # Get the question ID
        short_id = result.get("short_id") or result.get("question_id_short", "")
        if not short_id:
            return ""
            
        return f"{self.ui_url}/question/{short_id}"
    
    def _sanitize_tweet(self, tweet: str) -> str:
        """
        Sanitize a tweet
        
        Args:
            tweet: Raw tweet text
            
        Returns:
            Sanitized tweet text
        """
        # Decode HTML entities
        tweet = html.unescape(tweet)
        
        # Ensure the tweet is not too long
        if len(tweet) > self.max_length:
            tweet = tweet[:self.max_length - 3] + "..."
            
        return tweet
        
    def get_tags_for_result(self, result: Dict[str, Any]) -> List[str]:
        """
        Get tags for a result
        
        Args:
            result: Oracle result data
            
        Returns:
            List of tags
        """
        tags = result.get("tags", [])
        if not tags:
            tags = result.get("proposal_metadata", {}).get("tags", [])
            
        return [tag for tag in tags if tag]


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Create a sample result
    sample_result = {
        "query_id": "0x024e024afcbaf99e7d295f5017eea2398c6bc718e56063abfea70cdc5ed43934",
        "short_id": "024e024a",
        "recommendation": "p2",
        "tags": ["Crypto", "Ethereum", "eth", "Crypto Prices", "2025 Predictions"],
        "proposal_metadata": {
            "ancillary_data": "q: title: Will Ethereum dip to $1,500 by December 31?, description: This market will immediately resolve to \"Yes\" if any Binance 1 minute candle for Ethereum (ETHUSDT) between December 30, 2024, 21:00 and December 31, 2025, 23:59 in the ET timezone has a final \"Low\" price of $1,500.00 or lower. Otherwise, this market will resolve to \"No.\""
        }
    }
    
    # Create a generator and test it
    generator = TweetContentGenerator()
    tweet = generator.generate_tweet(sample_result)
    print(f"Generated tweet:\n{tweet}")
    
    # Test batch generation
    batch_tweets = generator.generate_batch([sample_result] * 3)
    print(f"\nGenerated {len(batch_tweets)} tweets in batch")
    
    # Test summary generation
    summary = generator.generate_outcome_summary([sample_result] * 5)
    print(f"\nGenerated summary:\n{summary}")