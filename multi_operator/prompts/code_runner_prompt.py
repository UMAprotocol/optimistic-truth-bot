#!/usr/bin/env python3
"""
Code Runner prompt creation utilities for UMA Multi-Operator System.
This module provides functions to generate prompts for the Code Runner solver.
"""

from typing import Dict, Any, Optional, List, Set


def get_first_attempt_prompt(
    user_prompt: str,
    query_type: str,
    available_api_keys: Set[str],
    data_sources: Optional[Dict[str, Any]] = None,
    template_code: Optional[str] = None,
) -> str:
    """
    Generate the prompt for the first code generation attempt.

    Args:
        user_prompt: The user prompt to solve
        query_type: The type of query (crypto, sports_mlb, etc.)
        available_api_keys: Set of available API keys
        data_sources: Optional dictionary of data sources
        template_code: Optional template code to use as reference

    Returns:
        The prompt for code generation
    """
    # First attempt uses template as reference
    code_gen_prompt = f"""You are an expert Python programmer. I need you to generate code to solve the following prediction market question:

{user_prompt}

Please write Python code that will gather the necessary data to answer this question definitively.

IMPORTANT REQUIREMENTS:
1. DO NOT use command-line arguments. Extract all necessary information from the question itself.
2. Load environment variables from .env files using the python-dotenv package.
3. For API keys, use the following environment variables:
"""
    # Add information about all available API keys and data sources
    for api_key_name in sorted(available_api_keys):
        code_gen_prompt += f"   - {api_key_name}\n"
        
    code_gen_prompt += "\n4. Available Data Sources Information:\n"
    
    # Add information about data sources if available
    if data_sources:
        # Add data source information based on the query type
        if query_type == "crypto":
            crypto_sources = [s for s in data_sources.values() if s.get("category") == "crypto"]
            if crypto_sources:
                code_gen_prompt += "   Cryptocurrency Data Sources:\n"
                for source in crypto_sources:
                    name = source.get("name", "Unknown")
                    code_gen_prompt += f"   - {name}:\n"
                    
                    # Add endpoints information
                    if "endpoints" in source:
                        for endpoint_type, url in source["endpoints"].items():
                            code_gen_prompt += f"     * {endpoint_type}: {url}\n"
                            
                            # Add specific usage examples for Binance proxy
                            if "proxy" in endpoint_type.lower() and "binance" in url.lower():
                                code_gen_prompt += "     * RECOMMENDED: Use this proxy endpoint first for better reliability\n"
                                code_gen_prompt += f"     * Example: {url}?symbol=BTCUSDT&interval=1m&limit=1&startTime=TIMESTAMP&endTime=TIMESTAMP\n"
        
        elif query_type == "sports_mlb" or query_type.startswith("sports_"):
            sports_type = query_type.replace("sports_", "").upper()
            sports_sources = [
                s for s in data_sources.values() 
                if s.get("category") == "sports" and 
                (sports_type in s.get("name", "") or sports_type in s.get("subcategory", ""))
            ]
            
            if sports_sources:
                code_gen_prompt += f"   Sports Data Sources for {sports_type}:\n"
                for source in sports_sources:
                    name = source.get("name", "Unknown")
                    code_gen_prompt += f"   - {name}:\n"
                    
                    # Add endpoints information
                    if "endpoints" in source:
                        for endpoint_type, url in source["endpoints"].items():
                            code_gen_prompt += f"     * {endpoint_type}: {url}\n"

    code_gen_prompt += """
5. NEVER include actual API key values in the code, always load them from environment variables.

The code should be completely self-contained and runnable with no arguments.

"""
    if template_code:
        code_gen_prompt += f"""
Here's a similar code example that you can use as reference:

```python
{template_code}
```

MODIFY THE ABOVE TEMPLATE by:
1. Removing all command-line argument handling
2. Using dotenv to load API keys from environment variables
3. Extracting required info (dates, teams, etc.) directly from the question
4. Making the code runnable with no arguments
5. Handling errors gracefully
6. Returning results in a clear format (either JSON or plaintext with a 'recommendation: X' line)
"""
    else:
        code_gen_prompt += """
Your code should:
1. Import all necessary libraries including python-dotenv for loading environment variables
2. Load API keys from environment variables, NOT hardcoded
3. Extract required parameters (dates, teams, etc.) directly from the question
4. Make appropriate API calls to fetch data
5. Process the data to determine the answer
6. Handle errors gracefully
7. Return results in a clear format (either JSON or plaintext with a 'recommendation: X' line)
"""

    return code_gen_prompt


def get_retry_prompt(
    user_prompt: str,
    query_type: str,
    available_api_keys: Set[str],
    attempt: int,
) -> str:
    """
    Generate the prompt for subsequent code generation attempts.

    Args:
        user_prompt: The user prompt to solve
        query_type: The type of query (crypto, sports_mlb, etc.)
        available_api_keys: Set of available API keys
        attempt: Current attempt number

    Returns:
        The prompt for code generation
    """
    # Subsequent attempts provide the error and ask for fixes
    code_gen_prompt = f"""You previously generated Python code to solve this prediction market question, but it failed to execute correctly. Please fix the issues and provide an improved version.

Original question:
{user_prompt}

Previous code had the following issues:
- Failed on attempt {attempt-1}
- Common errors: 
  * Requiring command-line arguments
  * Hardcoded API keys
  * Incorrect imports
  * API connection issues
  * Incorrect use of RESOLUTION_MAP (using "p1" as a key instead of as a value)
  * KeyError exceptions when accessing dictionaries

Please provide a new, corrected version that:
1. DOES NOT use command-line arguments - extract all needed info from the question itself
2. Uses python-dotenv to load environment variables 
"""
    # Add information about all available API keys
    for api_key_name in sorted(available_api_keys):
        code_gen_prompt += f"   - {api_key_name}\n"
        
    code_gen_prompt += """
3. NEVER include actual API key values in the code, always load them from environment variables.
4. Makes the code runnable with no arguments
5. Handles errors more gracefully with try/except blocks
6. Returns results in a clear format: "recommendation: p1", "recommendation: p2", etc.
7. For sports data: Uses RESOLUTION_MAP correctly (keys are outcomes, values are recommendation codes)
"""

    return code_gen_prompt


def get_query_type_guidance(query_type: str, endpoint_info_getter=None) -> str:
    """
    Get guidance based on query type.

    Args:
        query_type: The type of query (crypto, sports_mlb, etc.)
        endpoint_info_getter: Optional function to get endpoint information

    Returns:
        Query-specific guidance
    """
    guidance = ""
    
    if query_type == "crypto":
        primary_endpoint = "Default Binance API endpoint"
        proxy_endpoint = "Not available"
        
        if endpoint_info_getter:
            primary_endpoint = endpoint_info_getter("crypto", "primary") or primary_endpoint
            proxy_endpoint = endpoint_info_getter("crypto", "proxy") or proxy_endpoint
            
        guidance = f"""
For cryptocurrency data:
- Use the Binance API to fetch historical prices (no API key required for public endpoints)
- Primary Binance API: {primary_endpoint}
{f"- Recommended proxy endpoint: {proxy_endpoint}" if proxy_endpoint != "Not available" else ""}
- Handle timeframe conversions between timezones carefully
- Make sure to use the correct symbol format (e.g., BTCUSDT)
- Extract dates and times from the question
"""
    elif query_type == "sports_mlb":
        guidance = """
For MLB sports data:
- Use Sports Data IO API with the SPORTS_DATA_IO_MLB_API_KEY from environment variables
- Use python-dotenv to load the API key: 
  ```python
  from dotenv import load_dotenv
  import os
  
  load_dotenv()
  api_key = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
  ```
- Extract team names and dates from the question
- Properly resolve outcomes based on game status
- IMPORTANT: When using RESOLUTION_MAP, the keys are outcome names and values are recommendation codes:
  ```python
  RESOLUTION_MAP = {
    "Blue Jays": "p1",   # Home team wins
    "Orioles": "p2",     # Away team wins  
    "50-50": "p3",       # Tie or undetermined
    "Too early to resolve": "p4"  # Not enough data
  }
  
  # CORRECT usage - use team/outcome names as keys:
  if home_team_wins:
      return "recommendation: " + RESOLUTION_MAP["Blue Jays"]   # Returns "recommendation: p1"
  elif away_team_wins:
      return "recommendation: " + RESOLUTION_MAP["Orioles"]     # Returns "recommendation: p2"
  
  # INCORRECT usage - DO NOT do this:
  # return RESOLUTION_MAP["p1"]  # This will cause KeyError: 'p1'
  ```
"""
    elif query_type == "sports_nhl":
        guidance = """
For NHL hockey data:
- Use Sports Data IO API with the SPORTS_DATA_IO_NHL_API_KEY from environment variables
- Use python-dotenv to load the API key:
  ```python
  from dotenv import load_dotenv
  import os
  
  load_dotenv()
  api_key = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
  ```
- Extract team names and dates from the question
- The team abbreviations for NHL are:
  * Seattle Kraken = SEA
  * Vegas Golden Knights = VGK
  * Toronto Maple Leafs = TOR
  * Boston Bruins = BOS
  * And other standard NHL team abbreviations
- CRITICALLY IMPORTANT: When defining RESOLUTION_MAP, you MUST use team abbreviations (not full names) as keys:
  ```python
  # CORRECT - Use team abbreviations as keys
  RESOLUTION_MAP = {
      "VGK": "p1",  # Golden Knights
      "SEA": "p2",  # Kraken
      "50-50": "p3",
      "Too early to resolve": "p4",
  }
  
  # WRONG - Do NOT use full team names as keys
  # RESOLUTION_MAP = {
  #     "Golden Knights": "p1",  # Wrong! Should use "VGK"
  #     "Kraken": "p2",          # Wrong! Should use "SEA"
  #     "50-50": "p3",
  #     "Too early to resolve": "p4",
  # }
  ```
- Map the outcome correctly using the resolution conditions in the query
# The examples below show how to use the RESOLUTION_MAP with team abbreviations:
  ```python
  # CORRECT - Use team abbreviations as keys
  RESOLUTION_MAP = {
      "VGK": "p1",  # Golden Knights
      "SEA": "p2",  # Kraken
      "50-50": "p3",
      "Too early to resolve": "p4",
  }
  
  # CORRECT usage - use team abbreviations as keys:
  if golden_knights_win:
      return "recommendation: " + RESOLUTION_MAP["VGK"]  # Returns "recommendation: p1"
  elif kraken_win:
      return "recommendation: " + RESOLUTION_MAP["SEA"]  # Returns "recommendation: p2"
  
  # INCORRECT usage - DO NOT do this:
  # return RESOLUTION_MAP["p1"]  # This will cause KeyError: 'p1'
  # DO NOT use full team names like "Golden Knights" or "Kraken" as keys
  ```
"""

    return guidance


def get_code_generation_prompt(
    user_prompt: str,
    query_type: str,
    available_api_keys: Set[str],
    data_sources: Optional[Dict[str, Any]] = None,
    template_code: Optional[str] = None,
    attempt: int = 1,
    endpoint_info_getter=None,
) -> str:
    """
    Generate the complete code generation prompt.

    Args:
        user_prompt: The user prompt to solve
        query_type: The type of query (crypto, sports_mlb, etc.)
        available_api_keys: Set of available API keys
        data_sources: Optional dictionary of data sources
        template_code: Optional template code to use as reference
        attempt: Current attempt number
        endpoint_info_getter: Optional function to get endpoint information

    Returns:
        The complete prompt for code generation
    """
    if attempt == 1:
        base_prompt = get_first_attempt_prompt(
            user_prompt, query_type, available_api_keys, data_sources, template_code
        )
    else:
        base_prompt = get_retry_prompt(
            user_prompt, query_type, available_api_keys, attempt
        )
    
    # Add query type specific guidance
    guidance = get_query_type_guidance(query_type, endpoint_info_getter)
    
    # Add final instructions
    final_instructions = """
IMPORTANT: Your code MUST run successfully without errors and without requiring any command-line arguments. Focus on robustness rather than features.
Return ONLY the Python code without explanation.
"""
    
    return base_prompt + guidance + final_instructions