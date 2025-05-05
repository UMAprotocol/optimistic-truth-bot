#!/usr/bin/env python3
"""
Logging Setup for the LLM Oracle Tweet Generator

This module provides functions for setting up logging for the tweet generator.
"""

import os
import sys
import logging
import logging.handlers
from typing import Dict, Any, Optional
from pathlib import Path

def setup_logging(
    config: Dict[str, Any],
    log_prefix: str = "tweet_generator",
    create_log_dir: bool = True
) -> logging.Logger:
    """
    Set up logging for the application
    
    Args:
        config: Configuration dictionary with logging settings
        log_prefix: Prefix for log files
        create_log_dir: Whether to create the log directory if it doesn't exist
        
    Returns:
        Root logger
    """
    # Get logging settings from config
    log_level_str = config.get("log_level", "INFO").upper()
    log_file = config.get("log_file")
    log_to_console = config.get("log_to_console", True)
    log_format = config.get("log_format", '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    log_max_bytes = config.get("log_max_bytes", 10 * 1024 * 1024)  # 10MB
    log_backup_count = config.get("log_backup_count", 5)
    
    # Convert log level string to logging level
    log_level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL
    }
    log_level = log_level_map.get(log_level_str, logging.INFO)
    
    # Create root logger and set level
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove existing handlers to avoid duplicate logging
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create formatter
    formatter = logging.Formatter(log_format)
    
    # Add console handler if requested
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    # Add file handler if log file is specified
    if log_file:
        log_path = Path(log_file)
        
        # Create log directory if needed
        if create_log_dir and not log_path.parent.exists():
            try:
                log_path.parent.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                print(f"Error creating log directory: {e}", file=sys.stderr)
                
        try:
            # Use rotating file handler to limit file size
            file_handler = logging.handlers.RotatingFileHandler(
                log_path,
                maxBytes=log_max_bytes,
                backupCount=log_backup_count
            )
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
        except Exception as e:
            print(f"Error setting up log file: {e}", file=sys.stderr)
            if log_to_console:
                console_handler.setLevel(logging.WARNING)
                root_logger.warning(f"Failed to set up log file: {e}")
    
    # Create a specific logger for the tweet generator
    logger = logging.getLogger(log_prefix)
    
    # Log the configuration
    logger.debug(f"Logging initialized with level {log_level_str}")
    if log_file:
        logger.debug(f"Logging to file: {log_file}")
    if log_to_console:
        logger.debug("Logging to console")
    
    return logger


def add_sentry_logging(config: Dict[str, Any], logger: logging.Logger) -> bool:
    """
    Add Sentry error tracking to the logging setup
    
    Args:
        config: Configuration dictionary
        logger: Logger to add Sentry to
        
    Returns:
        True if Sentry was configured successfully, False otherwise
    """
    sentry_dsn = config.get("sentry_dsn")
    if not sentry_dsn:
        return False
        
    try:
        import sentry_sdk
        from sentry_sdk.integrations.logging import LoggingIntegration
        
        # Configure Sentry SDK
        sentry_logging = LoggingIntegration(
            level=logging.WARNING,  # Capture warnings and above as breadcrumbs
            event_level=logging.ERROR  # Send errors as events
        )
        
        sentry_sdk.init(
            dsn=sentry_dsn,
            integrations=[sentry_logging],
            
            # Set traces_sample_rate to 1.0 to capture 100%
            # of transactions for performance monitoring.
            traces_sample_rate=config.get("sentry_traces_sample_rate", 0.1),
            
            # Environment name
            environment=config.get("environment", "development"),
            
            # Custom release name
            release=config.get("release_version", "0.1.0")
        )
        
        logger.info("Sentry error tracking configured")
        return True
        
    except ImportError:
        logger.warning("Sentry SDK not installed. Error tracking disabled.")
        return False
    except Exception as e:
        logger.error(f"Failed to configure Sentry: {e}")
        return False


def log_exception(logger: logging.Logger, exc: Exception, context: Optional[Dict[str, Any]] = None) -> None:
    """
    Log an exception with additional context
    
    Args:
        logger: Logger to use
        exc: Exception to log
        context: Additional context to include
    """
    if context is None:
        context = {}
        
    # Prepare the message
    message = f"Exception: {type(exc).__name__}: {str(exc)}"
    if context:
        message += f" | Context: {context}"
        
    # Log the exception with traceback
    logger.exception(message)
    
    # If Sentry is configured, add additional context
    try:
        import sentry_sdk
        if context:
            with sentry_sdk.configure_scope() as scope:
                for key, value in context.items():
                    scope.set_extra(key, value)
    except ImportError:
        pass


# Example usage
if __name__ == "__main__":
    # Example configuration
    config = {
        "log_level": "DEBUG",
        "log_file": "logs/tweet_generator.log",
        "log_to_console": True
    }
    
    # Set up logging
    logger = setup_logging(config)
    
    # Log some test messages
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    
    # Test exception logging
    try:
        1/0
    except Exception as e:
        log_exception(logger, e, {"operation": "test_division"})