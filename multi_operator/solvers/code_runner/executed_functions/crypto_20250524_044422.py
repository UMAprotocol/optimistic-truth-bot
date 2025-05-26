import requests
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Define the API endpoint for Dune Analytics
DUNE_ANALYTICS_URL = "https://dune.com/api/v1/chart/123456"  # Placeholder URL, replace with actual chart ID URL

def fetch_graduated_tokens_count(date):
    """
    Fetches the count of graduated tokens created on a specific date from Dune Analytics.

    Args:
        date (str): Date in 'YYYY-MM-DD' format.

    Returns:
        int: Number of graduated tokens or None if data cannot be fetched.
    """
    try:
        # Construct the request URL with the specific date
        url = f"{DUNE_ANALYTICS_URL}?date={date}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        # Assuming the data structure has a 'data' key and the count is directly accessible
        # This will need to be adjusted based on the actual API response structure
        tokens_count = data['data']['count']
        return tokens_count
    except Exception as e:
        print(f"Failed to fetch data: {str(e)}")
        return None

def resolve_market(date):
    """
    Resolves the market based on the number of graduated tokens created on a specific date.

    Args:
        date (str): Date in 'YYYY-MM-DD' format.

    Returns:
        str: Market resolution recommendation.
    """
    tokens_count = fetch_graduated_tokens_count(date)
    
    if tokens_count is None:
        return "recommendation: p3"  # Unknown/50-50 if data cannot be fetched
    elif tokens_count >= 271:
        return "recommendation: p2"  # Yes, if 271 or more tokens were created
    else:
        return "recommendation: p1"  # No, if fewer than 271 tokens were created

def main():
    # The specific date for the market resolution
    market_date = "2025-05-23"
    
    # Resolve the market based on the token count for the given date
    resolution = resolve_market(market_date)
    print(resolution)

if __name__ == "__main__":
    main()