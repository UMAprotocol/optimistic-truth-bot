#!/usr/bin/env python3
"""
Oracle API Client

This module provides a client for interacting with the LLM Oracle API.
"""

import os
import time
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
import requests
from dotenv import load_dotenv

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
        self.base_url = base_url or os.getenv("ORACLE_API_URL", "https://api.ai.uma.xyz")
        self.logger = logging.getLogger("oracle_api_client")
        self.session = requests.Session()
        self.cache = {}
        self.cache_duration = 300  # Cache results for 5 minutes
    
    def get_health(self) -> Dict[str, Any]:
        """
        Check API health
        
        Returns:
            API health status
        """
        response = self.session.get(f"{self.base_url}/")
        response.raise_for_status()
        return response.json()
    
    def query_recent_results(self, 
                            hours: int = 24, 
                            limit: int = 20, 
                            recommendation: Optional[str] = None, 
                            tags: Optional[List[str]] = None,
                            cache: bool = True) -> List[Dict[str, Any]]:
        """
        Query recent results from the API
        
        Args:
            hours: Number of hours to look back
            limit: Maximum number of results to return
            recommendation: Filter by recommendation (p1, p2, p3, p4)
            tags: Filter by tags
            cache: Whether to use the cache
            
        Returns:
            List of recent results
        """
        # Calculate timestamps
        end_timestamp = int(time.time())
        start_timestamp = end_timestamp - (hours * 3600)
        
        # Check cache
        cache_key = f"recent_results_{hours}_{limit}_{recommendation}_{tags}"
        if cache and cache_key in self.cache:
            cache_entry = self.cache[cache_key]
            if time.time() - cache_entry["timestamp"] < self.cache_duration:
                self.logger.debug(f"Using cached results for {cache_key}")
                return cache_entry["data"]
        
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
            for tag in tags:
                params.setdefault("tags", []).append(tag)
            
        self.logger.info(f"Querying API for results since {datetime.fromtimestamp(start_timestamp)}")
        
        # Make the API request
        try:
            response = self.session.get(f"{self.base_url}/api/advanced-query", params=params)
            response.raise_for_status()
            results = response.json()
            self.logger.info(f"Found {len(results)} results")
            
            # Update cache
            if cache:
                self.cache[cache_key] = {
                    "timestamp": time.time(),
                    "data": results
                }
                
            return results
        except requests.RequestException as e:
            self.logger.error(f"API request failed: {e}")
            return []

    def get_experiment_results(self, experiment_id: str, limit: int = 100, cache: bool = True) -> List[Dict[str, Any]]:
        """
        Get results for a specific experiment
        
        Args:
            experiment_id: ID of the experiment
            limit: Maximum number of results to return
            cache: Whether to use the cache
            
        Returns:
            List of experiment results
        """
        # Check cache
        cache_key = f"experiment_{experiment_id}_{limit}"
        if cache and cache_key in self.cache:
            cache_entry = self.cache[cache_key]
            if time.time() - cache_entry["timestamp"] < self.cache_duration:
                self.logger.debug(f"Using cached results for {cache_key}")
                return cache_entry["data"]
        
        try:
            response = self.session.get(
                f"{self.base_url}/api/experiment/{experiment_id}",
                params={"limit": limit, "full": "true"}
            )
            response.raise_for_status()
            results = response.json()
            
            # Update cache
            if cache:
                self.cache[cache_key] = {
                    "timestamp": time.time(),
                    "data": results
                }
                
            return results
        except requests.RequestException as e:
            self.logger.error(f"Failed to get experiment results: {e}")
            return []
            
    def get_question_result(self, question_id: str, cache: bool = True) -> Optional[Dict[str, Any]]:
        """
        Get result for a specific question
        
        Args:
            question_id: ID of the question
            cache: Whether to use the cache
            
        Returns:
            Question result or None if not found
        """
        # Check cache
        cache_key = f"question_{question_id}"
        if cache and cache_key in self.cache:
            cache_entry = self.cache[cache_key]
            if time.time() - cache_entry["timestamp"] < self.cache_duration:
                self.logger.debug(f"Using cached results for {cache_key}")
                return cache_entry["data"]
        
        try:
            response = self.session.get(
                f"{self.base_url}/api/question/{question_id}",
                params={"full": "true"}
            )
            response.raise_for_status()
            result = response.json()
            
            # Update cache
            if cache:
                self.cache[cache_key] = {
                    "timestamp": time.time(),
                    "data": result
                }
                
            return result
        except requests.RequestException as e:
            self.logger.error(f"Failed to get question result: {e}")
            return None
            
    def basic_query(self, 
                    query_id: Optional[str] = None, 
                    condition_id: Optional[str] = None, 
                    transaction_hash: Optional[str] = None, 
                    limit: int = 10,
                    full: bool = True,
                    cache: bool = True) -> List[Dict[str, Any]]:
        """
        Perform a basic query by ID
        
        Args:
            query_id: Filter by query_id (exact match)
            condition_id: Filter by condition_id (exact match)
            transaction_hash: Filter by transaction hash (exact match)
            limit: Maximum number of results to return
            full: Return full JSON if true, reduced version if false
            cache: Whether to use the cache
            
        Returns:
            List of matching results
        """
        # Check if at least one parameter is provided
        if not any([query_id, condition_id, transaction_hash]):
            self.logger.error("At least one of query_id, condition_id, or transaction_hash must be provided")
            return []
            
        # Check cache
        cache_key = f"basic_query_{query_id}_{condition_id}_{transaction_hash}_{limit}_{full}"
        if cache and cache_key in self.cache:
            cache_entry = self.cache[cache_key]
            if time.time() - cache_entry["timestamp"] < self.cache_duration:
                self.logger.debug(f"Using cached results for {cache_key}")
                return cache_entry["data"]
        
        # Build query parameters
        params = {"limit": limit, "full": "true" if full else "false"}
        
        if query_id:
            params["query_id"] = query_id
            
        if condition_id:
            params["condition_id"] = condition_id
            
        if transaction_hash:
            params["transaction_hash"] = transaction_hash
        
        try:
            response = self.session.get(f"{self.base_url}/api/query", params=params)
            response.raise_for_status()
            results = response.json()
            
            # Update cache
            if cache:
                self.cache[cache_key] = {
                    "timestamp": time.time(),
                    "data": results
                }
                
            return results
        except requests.RequestException as e:
            self.logger.error(f"API request failed: {e}")
            return []
            
    def advanced_query(self, 
                      identifier: Optional[str] = None,
                      start_timestamp: Optional[int] = None,
                      end_timestamp: Optional[int] = None,
                      ancillary_data: Optional[str] = None,
                      tags: Optional[List[str]] = None,
                      recommendation: Optional[str] = None,
                      limit: int = 10,
                      full: bool = True,
                      cache: bool = True) -> List[Dict[str, Any]]:
        """
        Perform an advanced query
        
        Args:
            identifier: Filter by partial match on tags, query_id, condition_id, etc.
            start_timestamp: Filter by minimum request timestamp (Unix timestamp)
            end_timestamp: Filter by maximum request timestamp (Unix timestamp)
            ancillary_data: Filter by partial match on ancillary data
            tags: Filter by one or more tags
            recommendation: Filter by recommendation value (p1, p2, p3, p4)
            limit: Maximum number of results to return
            full: Return full JSON if true, reduced version if false
            cache: Whether to use the cache
            
        Returns:
            List of matching results
        """
        # Check if at least one parameter is provided
        if not any([identifier, start_timestamp, end_timestamp, ancillary_data, tags, recommendation]):
            self.logger.error("At least one filter parameter must be provided")
            return []
            
        # Check cache
        cache_key = f"advanced_query_{identifier}_{start_timestamp}_{end_timestamp}_{ancillary_data}_{tags}_{recommendation}_{limit}_{full}"
        if cache and cache_key in self.cache:
            cache_entry = self.cache[cache_key]
            if time.time() - cache_entry["timestamp"] < self.cache_duration:
                self.logger.debug(f"Using cached results for {cache_key}")
                return cache_entry["data"]
        
        # Build query parameters
        params = {"limit": limit, "full": "true" if full else "false"}
        
        if identifier:
            params["identifier"] = identifier
            
        if start_timestamp:
            params["start_timestamp"] = start_timestamp
            
        if end_timestamp:
            params["end_timestamp"] = end_timestamp
            
        if ancillary_data:
            params["ancillary_data"] = ancillary_data
            
        if tags:
            for tag in tags:
                params.setdefault("tags", []).append(tag)
            
        if recommendation:
            params["recommendation"] = recommendation
        
        try:
            response = self.session.get(f"{self.base_url}/api/advanced-query", params=params)
            response.raise_for_status()
            results = response.json()
            
            # Update cache
            if cache:
                self.cache[cache_key] = {
                    "timestamp": time.time(),
                    "data": results
                }
                
            return results
        except requests.RequestException as e:
            self.logger.error(f"API request failed: {e}")
            return []
    
    def clear_cache(self):
        """Clear the cache"""
        self.cache = {}
        self.logger.debug("Cache cleared")
        
    def set_cache_duration(self, seconds: int):
        """
        Set the cache duration
        
        Args:
            seconds: Cache duration in seconds
        """
        self.cache_duration = seconds
        self.logger.debug(f"Cache duration set to {seconds} seconds")


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    client = OracleApiClient()
    
    # Check API health
    try:
        health = client.get_health()
        print(f"API health: {health}")
    except Exception as e:
        print(f"API health check failed: {e}")
        exit(1)
    
    # Get recent results
    results = client.query_recent_results(hours=24, limit=5)
    print(f"Found {len(results)} recent results")
    
    # Print the titles
    for result in results:
        ancillary_data = result.get("proposal_metadata", {}).get("ancillary_data", "")
        title_start = ancillary_data.find("title:")
        if title_start != -1:
            title_start += 6  # Length of "title:"
            title_end = ancillary_data.find(",", title_start)
            if title_end == -1:
                title_end = ancillary_data.find("\n", title_start)
            
            if title_end != -1:
                title = ancillary_data[title_start:title_end].strip()
                print(f"- {title}")
        else:
            print(f"- {result.get('question_id', 'Unknown')}")