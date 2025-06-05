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
    fixed_functions_config: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Generate the prompt for the first code generation attempt.

    Args:
        user_prompt: The user prompt to solve
        query_type: The type of query (crypto, sports_mlb, etc.)
        available_api_keys: Set of available API keys
        data_sources: Optional dictionary of data sources
        template_code: Optional template code to use as reference
        fixed_functions_config: Optional configuration for fixed execution functions

    Returns:
        The prompt for code generation
    """
    # First attempt uses template as reference
    code_gen_prompt = f"""You are an expert Python programmer. I need you to generate code to solve the following prediction market question:

{user_prompt}

Please write Python code that will gather the necessary data to answer this question definitively.

PREFERRED APPROACH - FIXED EXECUTION FUNCTIONS:
Before writing custom code, consider if this query can be solved using one of our pre-built, reliable fixed execution functions. These functions are battle-tested and should be preferred whenever possible:"""

    # Add fixed execution functions information
    if fixed_functions_config:
        code_gen_prompt += "\n\nAVAILABLE FIXED EXECUTION FUNCTIONS:\n"
        for func_name, func_info in fixed_functions_config.items():
            code_gen_prompt += f"\n{func_name}:\n"
            code_gen_prompt += f"  - Description: {func_info.get('description', 'No description')}\n"
            code_gen_prompt += f"  - Usage: {func_info.get('usage', 'No usage info')}\n"
            code_gen_prompt += f"  - Use cases:\n"
            for use_case in func_info.get('use_cases', []):
                code_gen_prompt += f"    * {use_case}\n"
        
        code_gen_prompt += "\nIf your query matches any of the above use cases, you should call the appropriate fixed function directly using subprocess rather than writing custom API code.\n"
        code_gen_prompt += "\nExample of calling a fixed function:\n"
        code_gen_prompt += """```python
import subprocess
import os

# Example: Using binance_price_query fixed function
def query_crypto_price(symbol, timestamp, timezone="US/Eastern"):
    try:
        result = subprocess.run([
            "python", "binance_price_query.py",
            "--symbol", symbol,
            "--timestamp", timestamp, 
            "--timezone", timezone,
            "--interval", "1h"
        ], capture_output=True, text=True, cwd="multi_operator/solvers/code_runner/fixed_execution_functions")
        
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            print(f"Fixed function failed: {result.stderr}")
            return None
    except Exception as e:
        print(f"Error calling fixed function: {e}")
        return None
```

ONLY use custom code generation if none of the fixed execution functions can solve your query.

IMPORTANT REQUIREMENTS FOR CUSTOM CODE:
1. DO NOT use command-line arguments. Extract all necessary information from the question itself.
2. Load environment variables from .env files using the python-dotenv package.
3. For API keys, use the following environment variables:
"""
    # Add information about all available API keys and data sources
    for api_key_name in sorted(available_api_keys):
        code_gen_prompt += f"   - {api_key_name}\n"
        
    code_gen_prompt += "\n4. Available Data Sources Information:\n"
    
    # Include ALL API keys and configuration information
    if data_sources:
        code_gen_prompt += "   ALL AVAILABLE API CONFIGURATIONS:\n"
        for source in data_sources.values():
            name = source.get("name", "Unknown")
            category = source.get("category", "Unknown")
            subcategory = source.get("subcategory", "")
            
            code_gen_prompt += f"   - {name} (Category: {category}"
            if subcategory:
                code_gen_prompt += f", Subcategory: {subcategory}"
            code_gen_prompt += "):\n"
            
            # Add API keys
            if "api_keys" in source:
                for api_key in source["api_keys"]:
                    code_gen_prompt += f"     * API Key: {api_key}\n"
            
            # Add endpoints
            if "endpoints" in source:
                for endpoint_type, url in source["endpoints"].items():
                    code_gen_prompt += f"     * {endpoint_type} endpoint: {url}\n"
    
    # Add query type specific information and more detailed examples
    code_gen_prompt += "\n5. Query Type Specific Information:\n\n"
    
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
                    has_proxy = False
                    primary_url = ""
                    proxy_url = ""
                    
                    if "endpoints" in source:
                        for endpoint_type, url in source["endpoints"].items():
                            code_gen_prompt += f"     * {endpoint_type}: {url}\n"
                            
                            if endpoint_type.lower() == "primary":
                                primary_url = url
                            
                            # Add specific usage examples for Binance proxy
                            if "proxy" in endpoint_type.lower():
                                has_proxy = True
                                proxy_url = url
                                code_gen_prompt += "     * RECOMMENDED: Use this proxy endpoint first for better reliability\n"
                                code_gen_prompt += f"     * Example: {url}?symbol=BTCUSDT&interval=1m&limit=1&startTime=TIMESTAMP&endTime=TIMESTAMP\n"
                    
                    # Add explicit instructions for fallback mechanism when proxy is available
                    if has_proxy and primary_url and proxy_url:
                        code_gen_prompt += """
     * CRITICALLY IMPORTANT: Since a proxy endpoint is provided, you MUST implement a fallback mechanism:
       1. Try the proxy endpoint first (better reliability)
       2. If proxy fails (timeout, error response, etc.), automatically fall back to the primary endpoint
       3. Your code MUST handle this gracefully with try/except blocks

     Example fallback code structure:
     ```python
     def get_data(symbol, start_time, end_time):
         try:
             # First try the proxy endpoint
             response = requests.get(f"{proxy_url}?symbol={symbol}&interval=1m&limit=1&startTime={start_time}&endTime={end_time}", timeout=10)
             response.raise_for_status()
             return response.json()
         except Exception as e:
             print(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
             # Fall back to primary endpoint if proxy fails
             response = requests.get(f"{primary_url}/klines?symbol={symbol}&interval=1m&limit=1&startTime={start_time}&endTime={end_time}", timeout=10)
             response.raise_for_status()
             return response.json()
     ```
     """
        
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
                    has_proxy = False
                    primary_url = ""
                    proxy_url = ""
                    
                    if "endpoints" in source:
                        for endpoint_type, url in source["endpoints"].items():
                            code_gen_prompt += f"     * {endpoint_type}: {url}\n"
                            
                            if endpoint_type.lower() == "primary":
                                primary_url = url
                            
                            if "proxy" in endpoint_type.lower():
                                has_proxy = True
                                proxy_url = url
                                code_gen_prompt += "     * RECOMMENDED: Use this proxy endpoint first for better reliability\n"
                    
                    # Add explicit instructions for fallback mechanism when proxy is available
                    if has_proxy and primary_url and proxy_url:
                        code_gen_prompt += """
     * CRITICALLY IMPORTANT: Since a proxy endpoint is provided, you MUST implement a fallback mechanism:
       1. Try the proxy endpoint first (better reliability)
       2. If proxy fails (timeout, error response, etc.), automatically fall back to the primary endpoint
       3. Your code MUST handle this gracefully with try/except blocks
     """

    code_gen_prompt += """
6. NEVER include actual API key values in the code, always load them from environment variables.

7. IMPORTANT FOR ALL DATA SOURCES: If a proxy endpoint is provided alongside a primary endpoint, you MUST implement the fallback mechanism described above. This is critical for reliability:
   - Always try the proxy endpoint first
   - If the proxy fails, fall back to the primary endpoint
   - Use appropriate timeout values (10 seconds recommended)
   - Include proper error handling with try/except blocks

The code should be completely self-contained and runnable with no arguments.

"""
    # ALWAYS include template code, guaranteeing a full example is provided
    if template_code:
        code_gen_prompt += f"""
Here's a complete code example that shows how to solve this type of problem:

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
    data_sources: Optional[Dict[str, Any]] = None,
    template_code: Optional[str] = None,
    fixed_functions_config: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Generate the prompt for subsequent code generation attempts.

    Args:
        user_prompt: The user prompt to solve
        query_type: The type of query (crypto, sports_mlb, etc.)
        available_api_keys: Set of available API keys
        attempt: Current attempt number
        data_sources: Optional dictionary of data sources
        template_code: Optional template code to use as reference
        fixed_functions_config: Optional configuration for fixed execution functions

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
  * Not implementing fallback mechanism for proxy endpoints
  * Not leveraging available fixed execution functions

FIRST - CHECK FIXED EXECUTION FUNCTIONS:
Before writing custom code again, reconsider using our pre-built fixed execution functions:"""

    # Add fixed execution functions information for retry
    if fixed_functions_config:
        code_gen_prompt += "\n\nAVAILABLE FIXED EXECUTION FUNCTIONS:\n"
        for func_name, func_info in fixed_functions_config.items():
            code_gen_prompt += f"\n{func_name}:\n"
            code_gen_prompt += f"  - Description: {func_info.get('description', 'No description')}\n"
            code_gen_prompt += f"  - Usage: {func_info.get('usage', 'No usage info')}\n"
            code_gen_prompt += f"  - Use cases:\n"
            for use_case in func_info.get('use_cases', []):
                code_gen_prompt += f"    * {use_case}\n"
        
        code_gen_prompt += "\nThese functions are more reliable than custom code. Use them if possible!\n"
    
    code_gen_prompt += """
Please provide a new, corrected version that:
1. FIRST considers using fixed execution functions via subprocess calls
2. DOES NOT use command-line arguments - extract all needed info from the question itself
3. Uses python-dotenv to load environment variables 
"""
    # Add information about all available API keys
    for api_key_name in sorted(available_api_keys):
        code_gen_prompt += f"   - {api_key_name}\n"
    
    # Include ALL API keys and configuration information
    if data_sources:
        code_gen_prompt += "\n3. ALL AVAILABLE API CONFIGURATIONS:\n"
        for source in data_sources.values():
            name = source.get("name", "Unknown")
            category = source.get("category", "Unknown")
            subcategory = source.get("subcategory", "")
            
            code_gen_prompt += f"   - {name} (Category: {category}"
            if subcategory:
                code_gen_prompt += f", Subcategory: {subcategory}"
            code_gen_prompt += "):\n"
            
            # Add API keys
            if "api_keys" in source:
                for api_key in source["api_keys"]:
                    code_gen_prompt += f"     * API Key: {api_key}\n"
            
            # Add endpoints
            if "endpoints" in source:
                for endpoint_type, url in source["endpoints"].items():
                    code_gen_prompt += f"     * {endpoint_type} endpoint: {url}\n"
    
    # Add query type specific data sources
    if data_sources:
        code_gen_prompt += "\n4. Query Type Specific Information:\n"
        
        # Add data source information based on the query type
        if query_type == "crypto":
            crypto_sources = [s for s in data_sources.values() if s.get("category") == "crypto"]
            if crypto_sources:
                code_gen_prompt += "   Cryptocurrency Data Sources:\n"
                for source in crypto_sources:
                    name = source.get("name", "Unknown")
                    code_gen_prompt += f"   - {name}:\n"
                    
                    # Add endpoints information
                    has_proxy = False
                    primary_url = ""
                    proxy_url = ""
                    
                    if "endpoints" in source:
                        for endpoint_type, url in source["endpoints"].items():
                            code_gen_prompt += f"     * {endpoint_type}: {url}\n"
                            
                            if endpoint_type.lower() == "primary":
                                primary_url = url
                            
                            if "proxy" in endpoint_type.lower():
                                has_proxy = True
                                proxy_url = url
                                code_gen_prompt += "     * RECOMMENDED: Use this proxy endpoint first for better reliability\n"
                    
                    # Add explicit instructions for fallback mechanism when proxy is available
                    if has_proxy and primary_url and proxy_url:
                        code_gen_prompt += """
     * CRITICALLY IMPORTANT: You MUST implement a fallback mechanism for API calls:
       1. Try the proxy endpoint first
       2. If proxy fails, automatically fall back to the primary endpoint
       3. Handle this with proper try/except blocks

     Example fallback code structure:
     ```python
     def get_data(symbol, start_time, end_time):
         try:
             # First try the proxy endpoint
             response = requests.get(f"{proxy_url}?symbol={symbol}&interval=1m&limit=1&startTime={start_time}&endTime={end_time}", timeout=10)
             response.raise_for_status()
             return response.json()
         except Exception as e:
             print(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
             # Fall back to primary endpoint if proxy fails
             response = requests.get(f"{primary_url}/klines?symbol={symbol}&interval=1m&limit=1&startTime={start_time}&endTime={end_time}", timeout=10)
             response.raise_for_status()
             return response.json()
     ```
     """
        
        elif query_type.startswith("sports_"):
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
                    has_proxy = False
                    primary_url = ""
                    proxy_url = ""
                    
                    if "endpoints" in source:
                        for endpoint_type, url in source["endpoints"].items():
                            code_gen_prompt += f"     * {endpoint_type}: {url}\n"
                            
                            if endpoint_type.lower() == "primary":
                                primary_url = url
                            
                            if "proxy" in endpoint_type.lower():
                                has_proxy = True
                                proxy_url = url
                                code_gen_prompt += "     * RECOMMENDED: Use this proxy endpoint first for better reliability\n"
                    
                    # Add explicit instructions for fallback mechanism when proxy is available
                    if has_proxy and primary_url and proxy_url:
                        code_gen_prompt += """
     * CRITICALLY IMPORTANT: You MUST implement a fallback mechanism for API calls:
       1. Try the proxy endpoint first
       2. If proxy fails, automatically fall back to the primary endpoint
       3. Handle this with proper try/except blocks
"""
        
    code_gen_prompt += """
5. NEVER include actual API key values in the code, always load them from environment variables.
6. Makes the code runnable with no arguments
7. Handles errors more gracefully with try/except blocks
8. Returns results in a clear format: "recommendation: p1", "recommendation: p2", etc.
9. For sports data: Uses RESOLUTION_MAP correctly (keys are outcomes, values are recommendation codes)
10. IMPORTANT: If a proxy endpoint is provided alongside a primary endpoint, you MUST implement a fallback mechanism:
   - Always try the proxy endpoint first
   - If the proxy fails, fall back to the primary endpoint
   - Use appropriate timeout values (10 seconds recommended) 
   - Include proper error handling with try/except blocks
"""

    # ALWAYS include template code, guaranteeing a full example is provided
    if template_code:
        code_gen_prompt += f"""
Here's a complete code example that shows how to solve this type of problem:

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
    fixed_functions_config: Optional[Dict[str, Any]] = None,
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
        fixed_functions_config: Optional configuration for fixed execution functions

    Returns:
        The complete prompt for code generation
    """
    # Make sure we always have template code, even for retry attempts
    if attempt == 1:
        base_prompt = get_first_attempt_prompt(
            user_prompt, query_type, available_api_keys, data_sources, template_code, fixed_functions_config
        )
    else:
        base_prompt = get_retry_prompt(
            user_prompt, query_type, available_api_keys, attempt, data_sources, template_code, fixed_functions_config
        )
    
    # Add query type specific guidance
    guidance = get_query_type_guidance(query_type, endpoint_info_getter)
    
    # Add API keys summary section for better visibility
    api_keys_summary = "\nAVAILABLE API KEYS SUMMARY:\n"
    # Add all available API keys to the summary
    for api_key_name in sorted(available_api_keys):
        api_keys_summary += f"- {api_key_name}\n"
    
    # Add data sources summary if available
    if data_sources:
        api_keys_summary += "\nAVAILABLE DATA SOURCES:\n"
        for source_name, source in data_sources.items():
            name = source.get("name", source_name)
            category = source.get("category", "Unknown")
            api_keys_summary += f"- {name} (Category: {category})\n"
            
            # Add API keys for this source
            if "api_keys" in source:
                for api_key in source["api_keys"]:
                    api_keys_summary += f"  * API Key: {api_key}\n"
                    
            # Add endpoints info
            if "endpoints" in source:
                for endpoint_type, url in source["endpoints"].items():
                    api_keys_summary += f"  * {endpoint_type} endpoint: {url}\n"
    
    # Add final instructions
    final_instructions = f"""
{api_keys_summary}

IMPORTANT: Your code MUST run successfully without errors and without requiring any command-line arguments. Focus on robustness rather than features.

REMEMBER: If proxy endpoints are provided, you MUST implement the fallback mechanism described earlier. This is critical for reliability and must be handled correctly.

Return ONLY the Python code without explanation.
"""
    
    return base_prompt + guidance + final_instructions