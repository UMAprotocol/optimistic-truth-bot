#!/usr/bin/env python3
"""
Oracle Tweet Generator Scheduler

This module provides scheduling functionality to regularly check for new results and post tweets.
"""

import os
import sys
import time
import signal
import logging
import argparse
from typing import Dict, List, Any, Optional, Callable, Set
from datetime import datetime, timedelta
import json
import threading
from pathlib import Path

# Add parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from common import setup_logging

# Import tweet generator modules
from oracle_api_client import OracleApiClient
from tweet_content import TweetContentGenerator

class ScheduleManager:
    """
    Manager for scheduling tweet generation and posting
    """
    def __init__(self, 
                state_file: str = "tweet_state.json", 
                check_interval: int = 300,  # 5 minutes default
                recovery_interval: int = 60,  # 1 minute for retries
                tweet_cooldown: int = 3600,  # 1 hour cooldown between tweets
                max_tweets_per_day: int = 48,  # Max tweets per day
                results_lookback_hours: int = 24):  # Hours to look back for results
        """
        Initialize the schedule manager
        
        Args:
            state_file: Path to state file for persistence
            check_interval: Interval between checks in seconds
            recovery_interval: Interval for retry after error in seconds
            tweet_cooldown: Minimum time between tweets in seconds
            max_tweets_per_day: Maximum tweets to post per day
            results_lookback_hours: Hours to look back for results
        """
        self.state_file = Path(state_file)
        self.check_interval = check_interval
        self.recovery_interval = recovery_interval
        self.tweet_cooldown = tweet_cooldown
        self.max_tweets_per_day = max_tweets_per_day
        self.results_lookback_hours = results_lookback_hours
        
        self.logger = logging.getLogger("schedule_manager")
        self.running = False
        self.last_check_time = 0
        self.last_tweet_time = 0
        self.daily_tweet_count = 0
        self.tweet_history = set()
        self.error_count = 0
        self.max_error_count = 5
        self.state_lock = threading.Lock()
        
        # Load state
        self._load_state()
        
    def start(self, 
             api_client: OracleApiClient, 
             tweet_generator: TweetContentGenerator, 
             post_tweet_func: Callable[[str], bool]):
        """
        Start the scheduler
        
        Args:
            api_client: Oracle API client
            tweet_generator: Tweet content generator
            post_tweet_func: Function to post a tweet
        """
        self.running = True
        self.api_client = api_client
        self.tweet_generator = tweet_generator
        self.post_tweet_func = post_tweet_func
        
        # Set up signal handlers
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)
        
        self.logger.info("Starting tweet scheduler")
        
        # Start the main loop
        self._run_scheduled_checks()
    
    def stop(self):
        """Stop the scheduler"""
        self.logger.info("Stopping tweet scheduler")
        self.running = False
        self._save_state()
    
    def _run_scheduled_checks(self):
        """Main scheduler loop"""
        while self.running:
            try:
                current_time = time.time()
                
                # Check if it's time to run a check
                if current_time - self.last_check_time >= self.check_interval:
                    self.logger.info("Running scheduled check for new results")
                    self._check_and_tweet()
                    self.last_check_time = current_time
                    self.error_count = 0  # Reset error count on successful check
                
                # Sleep to avoid busy waiting
                time.sleep(1)
                
            except Exception as e:
                self.error_count += 1
                self.logger.error(f"Error in scheduler: {e}")
                
                if self.error_count >= self.max_error_count:
                    self.logger.critical(f"Too many errors ({self.error_count}), stopping scheduler")
                    self.stop()
                else:
                    # Use recovery interval after errors
                    self.logger.info(f"Retrying in {self.recovery_interval} seconds (error {self.error_count}/{self.max_error_count})")
                    time.sleep(self.recovery_interval)
    
    def _check_and_tweet(self):
        """Check for new results and post tweets if needed"""
        # Reset daily tweet count if it's a new day
        self._reset_daily_count_if_needed()
        
        # Check if we've reached the daily limit
        if self.daily_tweet_count >= self.max_tweets_per_day:
            self.logger.info(f"Daily tweet limit reached ({self.daily_tweet_count}/{self.max_tweets_per_day})")
            return
        
        # Check if we're in the cooldown period
        current_time = time.time()
        time_since_last_tweet = current_time - self.last_tweet_time
        if time_since_last_tweet < self.tweet_cooldown:
            self.logger.info(f"In cooldown period, {int(self.tweet_cooldown - time_since_last_tweet)} seconds remaining")
            return
        
        # Get recent results
        results = self.api_client.query_recent_results(
            hours=self.results_lookback_hours,
            limit=10
        )
        
        if not results:
            self.logger.info("No recent results found")
            return
        
        # Filter for results we haven't tweeted about yet
        new_results = [
            result for result in results
            if self._get_result_id(result) not in self.tweet_history
        ]
        
        if not new_results:
            self.logger.info("No new results to tweet about")
            return
        
        # Generate and post a tweet for the newest result
        newest_result = new_results[0]
        tweet_text = self.tweet_generator.generate_tweet(newest_result)
        
        success = self.post_tweet_func(tweet_text)
        if success:
            self.logger.info(f"Posted tweet: {tweet_text}")
            self.last_tweet_time = time.time()
            self.daily_tweet_count += 1
            self.tweet_history.add(self._get_result_id(newest_result))
            self._save_state()
        else:
            self.logger.warning("Failed to post tweet")
    
    def _get_result_id(self, result: Dict[str, Any]) -> str:
        """
        Get a unique ID for a result
        
        Args:
            result: Oracle result data
            
        Returns:
            Unique ID string
        """
        # Try different ID fields in order of preference
        for field in ["question_id", "short_id", "question_id_short", "query_id"]:
            if field in result and result[field]:
                return str(result[field])
                
        # Fallback to query_id in proposal_metadata
        if "proposal_metadata" in result and "query_id" in result["proposal_metadata"]:
            return str(result["proposal_metadata"]["query_id"])
            
        # Last resort, use the whole result as a string
        return str(hash(json.dumps(result, sort_keys=True)))
    
    def _reset_daily_count_if_needed(self):
        """Reset the daily tweet count if it's a new day"""
        current_day = datetime.now().date()
        last_tweet_day = datetime.fromtimestamp(self.last_tweet_time).date() if self.last_tweet_time > 0 else None
        
        if last_tweet_day is None or current_day > last_tweet_day:
            self.logger.info(f"Resetting daily tweet count (was {self.daily_tweet_count})")
            self.daily_tweet_count = 0
            self._save_state()
    
    def _load_state(self):
        """Load state from file"""
        if not self.state_file.exists():
            self.logger.info(f"State file {self.state_file} does not exist, using defaults")
            return
            
        try:
            with self.state_lock, open(self.state_file, 'r') as f:
                state = json.load(f)
                
                self.last_check_time = state.get("last_check_time", 0)
                self.last_tweet_time = state.get("last_tweet_time", 0)
                self.daily_tweet_count = state.get("daily_tweet_count", 0)
                self.tweet_history = set(state.get("tweet_history", []))
                
                self.logger.info(f"Loaded state: last_tweet_time={datetime.fromtimestamp(self.last_tweet_time)}, daily_count={self.daily_tweet_count}, history_size={len(self.tweet_history)}")
        except Exception as e:
            self.logger.error(f"Error loading state: {e}")
    
    def _save_state(self):
        """Save state to file"""
        try:
            state = {
                "last_check_time": self.last_check_time,
                "last_tweet_time": self.last_tweet_time,
                "daily_tweet_count": self.daily_tweet_count,
                "tweet_history": list(self.tweet_history)
            }
            
            with self.state_lock, open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
                
            self.logger.debug("Saved state to file")
        except Exception as e:
            self.logger.error(f"Error saving state: {e}")
    
    def _handle_signal(self, signum, frame):
        """Handle termination signals"""
        self.logger.info(f"Received signal {signum}, stopping gracefully")
        self.stop()


def tweet_function_stub(tweet_text: str) -> bool:
    """
    Stub function for posting tweets (for testing)
    
    Args:
        tweet_text: The text to tweet
        
    Returns:
        True for success
    """
    print(f"TWEET: {tweet_text}")
    return True


def main():
    """Main entrypoint for the scheduler"""
    parser = argparse.ArgumentParser(description="LLM Oracle Tweet Scheduler")
    parser.add_argument("--check-interval", type=int, default=300, help="Interval between checks in seconds")
    parser.add_argument("--tweet-cooldown", type=int, default=3600, help="Minimum time between tweets in seconds")
    parser.add_argument("--max-tweets", type=int, default=48, help="Maximum tweets per day")
    parser.add_argument("--state-file", type=str, default="tweet_state.json", help="Path to state file")
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], default="INFO", help="Logging level")
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(level=args.log_level, log_to_console=True)
    logger = logging.getLogger("scheduler_main")
    
    # Create API client
    api_client = OracleApiClient()
    
    # Create tweet generator
    tweet_generator = TweetContentGenerator()
    
    # Create scheduler
    scheduler = ScheduleManager(
        state_file=args.state_file,
        check_interval=args.check_interval,
        tweet_cooldown=args.tweet_cooldown,
        max_tweets_per_day=args.max_tweets
    )
    
    # Start the scheduler
    try:
        scheduler.start(api_client, tweet_generator, tweet_function_stub)
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    finally:
        scheduler.stop()


if __name__ == "__main__":
    main()