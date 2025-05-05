#!/usr/bin/env python3
"""
Configuration module for the LLM Oracle Tweet Generator.

This module provides functions for loading and validating the configuration from
environment variables, configuration files, or command-line arguments.
"""

import os
import sys
import json
import logging
import argparse
from typing import Dict, Any, Optional
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Default configuration values
DEFAULT_CONFIG = {
    # API settings
    "oracle_api_url": "https://api.ai.uma.xyz",
    "oracle_ui_url": "",
    
    # Twitter API settings
    "twitter_api_key": "",
    "twitter_api_secret": "",
    "twitter_access_token": "",
    "twitter_access_token_secret": "",
    "twitter_bearer_token": "",
    "twitter_test_mode": False,
    "twitter_demo_mode": False,
    
    # Tweet generation settings
    "include_hashtags": True,
    "include_links": True,
    "max_tweet_length": 280,
    
    # Scheduler settings
    "check_interval": 300,  # 5 minutes
    "tweet_cooldown": 3600,  # 1 hour
    "max_tweets_per_day": 48,
    "results_lookback_hours": 24,
    "state_file": "tweet_state.json",
    
    # Logging settings
    "log_level": "INFO",
    "log_file": "tweet_generator.log",
    "log_to_console": True
}


class ConfigurationError(Exception):
    """Exception raised for configuration errors."""
    pass


def load_config(config_file: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from config file and environment variables.
    
    Args:
        config_file: Path to the configuration file (optional)
        
    Returns:
        Dictionary with configuration values
    
    Raises:
        ConfigurationError: If the configuration file cannot be loaded or parsed
    """
    config = DEFAULT_CONFIG.copy()
    logger = logging.getLogger("config")
    
    # Load from config file if provided
    if config_file:
        path = Path(config_file)
        if path.exists():
            try:
                with open(path, 'r') as f:
                    file_config = json.load(f)
                    config.update(file_config)
                logger.info(f"Loaded configuration from {config_file}")
            except json.JSONDecodeError as e:
                raise ConfigurationError(f"Invalid JSON in config file: {e}")
            except Exception as e:
                raise ConfigurationError(f"Error loading config file: {e}")
        else:
            logger.warning(f"Config file {config_file} not found, using defaults and environment variables")
    
    # Override with environment variables
    env_vars = {
        "ORACLE_API_URL": "oracle_api_url",
        "ORACLE_UI_URL": "oracle_ui_url",
        "TWITTER_API_KEY": "twitter_api_key",
        "TWITTER_API_SECRET": "twitter_api_secret",
        "TWITTER_ACCESS_TOKEN": "twitter_access_token",
        "TWITTER_ACCESS_TOKEN_SECRET": "twitter_access_token_secret",
        "TWITTER_BEARER_TOKEN": "twitter_bearer_token",
        "TWITTER_TEST_MODE": "twitter_test_mode",
        "TWITTER_DEMO_MODE": "twitter_demo_mode",
        "TWEET_CHECK_INTERVAL": "check_interval",
        "TWEET_COOLDOWN": "tweet_cooldown",
        "TWEET_MAX_PER_DAY": "max_tweets_per_day",
        "TWEET_LOOKBACK_HOURS": "results_lookback_hours",
        "TWEET_STATE_FILE": "state_file",
        "LOG_LEVEL": "log_level",
        "LOG_FILE": "log_file"
    }
    
    for env_var, config_key in env_vars.items():
        value = os.getenv(env_var)
        if value is not None:
            # Convert string values to appropriate types
            if config_key in ["check_interval", "tweet_cooldown", "max_tweets_per_day", "results_lookback_hours"]:
                try:
                    value = int(value)
                except ValueError:
                    logger.warning(f"Invalid value for {env_var}: {value}, must be an integer")
                    continue
            elif config_key in ["include_hashtags", "include_links", "log_to_console", "twitter_test_mode", "twitter_demo_mode"]:
                value = value.lower() in ["true", "yes", "1", "t", "y"]
                
            config[config_key] = value
            logger.debug(f"Set {config_key} from environment variable {env_var}")
    
    return config


def update_config_from_args(config: Dict[str, Any], args: argparse.Namespace) -> Dict[str, Any]:
    """
    Update configuration with command-line arguments.
    
    Args:
        config: Current configuration dictionary
        args: Parsed command-line arguments
        
    Returns:
        Updated configuration dictionary
    """
    # Map of argument names to config keys
    arg_map = {
        "api_url": "oracle_api_url",
        "ui_url": "oracle_ui_url",
        "check_interval": "check_interval",
        "tweet_cooldown": "tweet_cooldown",
        "max_tweets": "max_tweets_per_day",
        "lookback_hours": "results_lookback_hours",
        "state_file": "state_file",
        "log_level": "log_level",
        "log_file": "log_file",
        "log_to_console": "log_to_console",
        "include_hashtags": "include_hashtags",
        "include_links": "include_links",
        "demo_mode": "twitter_demo_mode",
        "test_mode": "twitter_test_mode"
    }
    
    # Update config with values from args
    for arg_name, config_key in arg_map.items():
        if hasattr(args, arg_name) and getattr(args, arg_name) is not None:
            config[config_key] = getattr(args, arg_name)
    
    return config


def validate_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate configuration values and set defaults for missing values.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Validated configuration dictionary
        
    Raises:
        ConfigurationError: If required configuration values are missing or invalid
    """
    # Ensure API URL is set
    if not config.get("oracle_api_url"):
        raise ConfigurationError("Oracle API URL is not configured")
        
    # Check Twitter API credentials for completeness if not in demo or test mode
    if not config.get("twitter_demo_mode") and not config.get("twitter_test_mode"):
        twitter_v1_keys = ["twitter_api_key", "twitter_api_secret", "twitter_access_token", "twitter_access_token_secret"]
        has_v1_creds = all(config.get(key) for key in twitter_v1_keys)
        has_v2_creds = bool(config.get("twitter_bearer_token"))
        
        if not has_v1_creds and not has_v2_creds:
            logging.warning(
                "Twitter API credentials are not fully configured and demo mode is not enabled. " +
                "Tweets will be generated but may not be posted to Twitter."
            )
    
    # Validate integer values
    int_keys = ["check_interval", "tweet_cooldown", "max_tweets_per_day", "results_lookback_hours"]
    for key in int_keys:
        if key in config:
            if not isinstance(config[key], int) or config[key] <= 0:
                raise ConfigurationError(f"{key} must be a positive integer")
    
    # Ensure state file is set
    if not config.get("state_file"):
        config["state_file"] = DEFAULT_CONFIG["state_file"]
        
    # Validate log level
    log_level = config.get("log_level", "").upper()
    if log_level not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
        config["log_level"] = DEFAULT_CONFIG["log_level"]
        
    return config


def add_config_arguments(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    """
    Add configuration-related arguments to an argument parser.
    
    Args:
        parser: ArgumentParser instance
        
    Returns:
        ArgumentParser with added arguments
    """
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument("--api-url", help="Oracle API URL")
    parser.add_argument("--ui-url", help="Oracle UI URL")
    parser.add_argument("--check-interval", type=int, help="Interval between checks in seconds")
    parser.add_argument("--tweet-cooldown", type=int, help="Minimum time between tweets in seconds")
    parser.add_argument("--max-tweets", type=int, help="Maximum tweets per day")
    parser.add_argument("--lookback-hours", type=int, help="Hours to look back for results")
    parser.add_argument("--state-file", help="Path to state file")
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], help="Logging level")
    parser.add_argument("--log-file", help="Path to log file")
    parser.add_argument("--log-to-console", action="store_true", help="Log to console")
    parser.add_argument("--no-log-to-console", dest="log_to_console", action="store_false", help="Don't log to console")
    parser.add_argument("--include-hashtags", action="store_true", help="Include hashtags in tweets")
    parser.add_argument("--no-hashtags", dest="include_hashtags", action="store_false", help="Don't include hashtags in tweets")
    parser.add_argument("--include-links", action="store_true", help="Include links in tweets")
    parser.add_argument("--no-links", dest="include_links", action="store_false", help="Don't include links in tweets")
    parser.add_argument("--demo-mode", action="store_true", help="Run in demo mode (don't actually post tweets, just log them)")
    parser.add_argument("--test-mode", action="store_true", help="Run in test mode with mock data")
    
    return parser


def save_config(config: Dict[str, Any], file_path: str) -> None:
    """
    Save configuration to a file.
    
    Args:
        config: Configuration dictionary
        file_path: Path to save the configuration file
        
    Raises:
        ConfigurationError: If the file cannot be written
    """
    try:
        with open(file_path, 'w') as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        raise ConfigurationError(f"Error saving configuration to {file_path}: {e}")


# Example usage
if __name__ == "__main__":
    # Basic logging configuration
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Parse arguments
    parser = argparse.ArgumentParser(description="LLM Oracle Tweet Generator Configuration")
    add_config_arguments(parser)
    parser.add_argument("--save", help="Save configuration to the specified file")
    args = parser.parse_args()
    
    try:
        # Load and validate config
        config = load_config(args.config)
        config = update_config_from_args(config, args)
        config = validate_config(config)
        
        if args.save:
            save_config(config, args.save)
            print(f"Configuration saved to {args.save}")
        else:
            # Print the configuration
            print("Configuration:")
            for key, value in config.items():
                if key in ["twitter_api_key", "twitter_api_secret", "twitter_access_token", "twitter_access_token_secret", "twitter_bearer_token"]:
                    if value:
                        value = "********"  # Mask sensitive values
                print(f"  {key}: {value}")
    except ConfigurationError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        sys.exit(1)