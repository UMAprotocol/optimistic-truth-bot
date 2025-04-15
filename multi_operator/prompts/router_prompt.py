#!/usr/bin/env python3
"""
Router prompt creation utilities for UMA Multi-Operator System.
This module provides functions to generate router prompts for ChatGPT to decide which solver to use.
"""

from typing import Dict, Any, List, Optional


def get_router_prompt(
    user_prompt: str,
    available_solvers: List[str],
    excluded_solvers: Optional[List[str]] = None,
    overseer_guidance: Optional[str] = None,
    data_sources: Optional[Dict[str, Any]] = None,
    available_api_keys: Optional[List[str]] = None,
    verbose: bool = False
) -> str:
    """
    Generate the router prompt for ChatGPT to decide which solver to use.

    Args:
        user_prompt: The user prompt to analyze
        available_solvers: List of available solvers
        excluded_solvers: List of solvers to exclude from consideration
        overseer_guidance: Additional guidance from the overseer
        data_sources: Dictionary of data sources with their detailed configuration
        available_api_keys: List of API keys available to the code_runner
        verbose: Whether to include verbose details

    Returns:
        The router prompt for ChatGPT
    """
    # If excluded_solvers is provided, filter available_solvers
    if excluded_solvers:
        effective_solvers = [
            s for s in available_solvers if s not in excluded_solvers
        ]
        # Ensure we have at least one solver
        if not effective_solvers:
            effective_solvers = ["perplexity"]
    else:
        effective_solvers = available_solvers

    solvers_str = ", ".join(effective_solvers)
    
    # Generate information about available data sources
    data_source_details = ""
    sports_guidelines = ""
    crypto_guidelines = ""
    data_source_examples = []
    categories = {}
    
    # Process data sources if available
    if data_sources:
        # Group data sources by category
        for source_name, source in data_sources.items():
            category = source.get("category", "other")
            if category not in categories:
                categories[category] = []
            categories[category].append(source)
        
        # Create details section for each category
        for category, sources in categories.items():
            data_source_details += f"  * Available {category.capitalize()} Data Sources:\n"
            
            for source in sources:
                name = source.get("name", "Unknown")
                description = source.get("description", "")
                subcategory = source.get("subcategory", "")
                
                # Add the source name and description
                source_info = f"    - {name}"
                if subcategory:
                    source_info += f" ({subcategory})"
                data_source_details += f"{source_info}: {description}\n"
                
                # Add endpoints info if available and verbose mode is on
                if "endpoints" in source and verbose:
                    endpoints = source["endpoints"]
                    for endpoint_type, url in endpoints.items():
                        data_source_details += f"      {endpoint_type}: {url}\n"
                
                # Collect example queries for guidelines
                if "example_queries" in source and isinstance(source["example_queries"], list):
                    for query in source["example_queries"]:
                        data_source_examples.append(query)
        
        # Create specific guidelines for different categories
        if "sports" in categories:
            sports_examples = []
            for source in categories["sports"]:
                subcategory = source.get("subcategory", "")
                name = source.get("name", "")
                if subcategory:
                    if "example_queries" in source and len(source["example_queries"]) > 0:
                        example = source["example_queries"][0]
                        sports_examples.append(f"{subcategory} (e.g., \"{example}\")")
                    else:
                        sports_examples.append(subcategory)
            
            if sports_examples:
                sports_guidelines = "\n  * Specifically for: " + ", ".join(sports_examples)
        
        # Create crypto guidelines
        if "crypto" in categories:
            crypto_examples = []
            for source in categories["crypto"]:
                if "example_queries" in source and len(source["example_queries"]) > 0:
                    crypto_examples.extend(source["example_queries"])
            
            if crypto_examples:
                crypto_guidelines = "\n  * Including: " + ", ".join([f'"{ex}"' for ex in crypto_examples[:2]])
    
    # Fall back to API key parsing if no data sources
    elif available_api_keys:
        # Keep track of which sports leagues are available
        available_sports = {
            "MLB": False,
            "NBA": False,
            "NFL": False,
            "NHL": False,
            "SOCCER": False,
            "NCAA": False
        }
        
        # Hard-coded check - force NHL to be included in the prompt
        # This is a critical fix to ensure router knows about NHL capabilities
        for api_key in available_api_keys:
            if "NHL" in api_key:
                available_sports["NHL"] = True
        
        # Explicit check for NHL API key
        if "SPORTS_DATA_IO_NHL_API_KEY" in available_api_keys:
            available_sports["NHL"] = True
        
        data_source_details = "  * Currently available data sources based on API keys:\n"
        
        # Always include NHL in data sources if we have the key in available_api_keys
        if any("NHL" in api_key for api_key in available_api_keys) or available_sports["NHL"]:
            data_source_details += "    - NHL (National Hockey League) data\n"
            available_sports["NHL"] = True
        
        # Process other API keys
        for api_key in available_api_keys:
            # Parse the API key to generate a human-readable description
            if "MLB" in api_key:
                data_source_details += "    - MLB (Major League Baseball) data\n"
                available_sports["MLB"] = True
            elif "NBA" in api_key:
                data_source_details += "    - NBA (National Basketball Association) data\n"
                available_sports["NBA"] = True
            elif "NFL" in api_key:
                data_source_details += "    - NFL (National Football League) data\n"
                available_sports["NFL"] = True
            elif "NHL" in api_key:
                # Already added above
                pass
            elif "SOCCER" in api_key or "FIFA" in api_key:
                data_source_details += "    - Soccer/Football data\n"
                available_sports["SOCCER"] = True
            elif "NCAA" in api_key:
                data_source_details += "    - NCAA (College sports) data\n"
                available_sports["NCAA"] = True
            elif "BINANCE" in api_key:
                data_source_details += "    - Binance cryptocurrency price data\n"
            elif not any(sport in api_key for sport in ["MLB", "NBA", "NFL", "NHL", "SOCCER", "NCAA", "BINANCE"]):
                # Generic entry for unrecognized keys
                data_source_details += f"    - {api_key.replace('_API_KEY', '').replace('SPORTS_DATA_IO_', '')} data\n"
        
        # Generate specific examples for the guidelines
        sports_examples = []
        for sport, available in available_sports.items():
            if available:
                if sport == "MLB":
                    sports_examples.append("MLB baseball games (e.g., \"Did the Yankees win yesterday?\")")
                elif sport == "NBA":
                    sports_examples.append("NBA basketball games (e.g., \"What was the Lakers score on Tuesday?\")")
                elif sport == "NFL":
                    sports_examples.append("NFL football games (e.g., \"Did the Eagles cover the spread against the Cowboys?\")")
                elif sport == "NHL":
                    sports_examples.append("NHL hockey games (e.g., \"Who won the Maple Leafs vs Bruins game?\" or \"Did the Kraken beat the Golden Knights?\")")
                elif sport == "SOCCER":
                    sports_examples.append("Soccer/Football matches (e.g., \"What was the score in the Manchester United game?\")")
                elif sport == "NCAA":
                    sports_examples.append("College sports (e.g., \"Did Duke win their last basketball game?\")")
        
        # Special case check for NHL in API keys or data sources to ensure it's included
        has_nhl_key = "SPORTS_DATA_IO_NHL_API_KEY" in available_api_keys
        has_nhl_source = False
        
        # Look for NHL in structured data sources
        if data_sources:
            for source_name, source in data_sources.items():
                if "NHL" in source_name or (source.get("subcategory") == "hockey"):
                    has_nhl_source = True
        
        if (has_nhl_key or has_nhl_source) and "NHL" not in [sport for sport, available in available_sports.items() if available]:
            sports_examples.append("NHL hockey games (e.g., \"Who won the Maple Leafs vs Bruins game?\" or \"Did the Kraken beat the Golden Knights?\")")
            available_sports["NHL"] = True
            # Also add to data source details if not already there
            if "NHL" not in data_source_details:
                data_source_details += "    - NHL (National Hockey League) data\n"
        
        # Force include NHL example if it was in the data sources but not picked up
        nhl_forced = False
        if data_sources:
            for source_name, source in data_sources.items():
                if "NHL" in source_name and "NHL" not in sports_guidelines:
                    nhl_forced = True
        
        if sports_examples:
            sports_guidelines = "\n  * Specifically for: " + ", ".join(sports_examples)
            
        # Add NHL if we forced it or if we have the NHL API key
        has_nhl_key = any("NHL" in api_key for api_key in available_api_keys) or "SPORTS_DATA_IO_NHL_API_KEY" in available_api_keys
        if (nhl_forced or has_nhl_key) and "hockey" not in sports_guidelines.lower():
            if sports_guidelines:
                sports_guidelines += ", NHL hockey games (e.g., \"Who won the Kraken vs Golden Knights game?\")"
            else:
                sports_guidelines = "\n  * Specifically for: NHL hockey games (e.g., \"Who won the Kraken vs Golden Knights game?\")"

    # Build the prompt
    prompt = f"""You are an expert router for UMA's optimistic oracle system. Your task is to analyze the provided query and decide which AI solver is best suited to handle it.

Available solvers: {solvers_str}

Solver descriptions:
- perplexity: Uses the Perplexity AI search engine to find information online to answer general questions. Best for:
  * Historical data and events
  * General knowledge questions requiring context
  * Questions needing interpretation of complex information
  * Has knowledge cutoff and may not have very recent information

- code_runner: Executes code to fetch real-time data from specific APIs. Currently supports:
  * Binance API: Can fetch cryptocurrency prices at specific times/dates with timezone conversion
  * Sports Data IO: Can retrieve sports data from various leagues
{data_source_details}  * Best for questions requiring precise, current data from these specific sources
  * Limited to only these data sources - cannot access other APIs or general information

USER PROMPT:
{user_prompt}

Please analyze the prompt carefully, considering:
1. The complexity of the query
2. The type of information needed
3. Whether the question requires specialized knowledge or data access
4. Whether the question specifically involves cryptocurrency prices or sports data
5. Whether multiple approaches might be complementary

IMPORTANT: You SHOULD select MULTIPLE solvers when appropriate. For complementary approaches, multiple solvers can provide different perspectives on the same question.
"""

    # Add overseer guidance if provided
    if overseer_guidance:
        prompt += f"""
OVERSEER GUIDANCE:
Based on previous attempts to solve this question, the overseer has provided the following guidance:
{overseer_guidance}

Please take this guidance into account when making your decision.
"""

    # If there are excluded solvers, explain why
    if excluded_solvers:
        excluded_str = ", ".join(excluded_solvers)
        prompt += f"""
NOTE: The following solvers have been EXCLUDED due to previous failures or overseer feedback: {excluded_str}
"""

    prompt += f"""
Return your answer in a specific format:
```decision
{{
  "solvers": ["solver_name1", "solver_name2"],
  "reason": "Brief explanation of why these solvers are best suited",
  "multi_solver_strategy": "Optional explanation of how these solvers complement each other"
}}
```

Where:
- solvers: Array of solver names selected from the available solvers
- reason: A brief explanation of why you selected these solvers
- multi_solver_strategy: If multiple solvers are selected, explain how they complement each other

Guidelines for solver selection:
- Use code_runner when the question specifically asks for:
  * Current or historical cryptocurrency prices from Binance (e.g., "What was the price of BTC on March 30th at 12pm ET?"){crypto_guidelines}
  * Sports data results, scores or team performance from available sources (e.g., "Did the Blue Jays win against the Orioles on April 1st?"){sports_guidelines}
  
- Use perplexity when the question requires:
  * General knowledge or context not limited to specific data points
  * Explanation or interpretation of events, rules, or concepts
  * Information beyond just crypto prices or MLB sports data
  
- Use both solvers when:
  * The question needs both factual data AND context/interpretation
  * Example: "Did BTC price increase after the news about XYZ on March 30th?" (code_runner for price data, perplexity for news context)
  * Example: "How did the Blue Jays perform compared to expectations in their April 1st game?" (code_runner for game data, perplexity for context about expectations)

Remember: code_runner is highly accurate for the supported data types but limited in scope. Perplexity has broader knowledge but may not have the most current information.
"""
    
    return prompt