import requests
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Define API endpoints
DUNE_ANALYTICS_URL = "https://dune.com/api/v1/chart/data"

# Load API keys from environment variables
DUNE_API_KEY = os.getenv("DUNE_API_KEY")

def fetch_graduated_tokens_count(date):
    """
    Fetch the count of graduated tokens on a specific date from Dune Analytics.
    
    Args:
        date (str): Date in 'YYYY-MM-DD' format.
    
    Returns:
        int: Number of graduated tokens or None if data cannot be fetched.
    """
    headers = {
        "x-dune-api-key": DUNE_API_KEY
    }
    params = {
        "chart_id": "chart_id_here",  # Replace with actual chart ID from Dune Analytics
        "date": date
    }
    try:
        response = requests.get(DUNE_ANALYTICS_URL, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        # Assuming the data structure contains a count of tokens
        return data['data']['count']
    except Exception as e:
        print(f"Failed to fetch data: {e}")
        return None

def resolve_market(date):
    """
    Resolve the market based on the number of graduated tokens created on a specific date.
    
    Args:
        date (str): Date in 'YYYY-MM-DD' format.
    
    Returns:
        str: Market resolution recommendation.
    """
    count = fetch_graduated_tokens_count(date)
    if count is None:
        return "recommendation: p3"  # Unknown/50-50 if data cannot be fetched
    elif count >= 271:
        return "recommendation: p2"  # Yes, if 271 or more tokens were created
    else:
        return "recommendation: p1"  # No, if fewer than 271 tokens were created

def main():
    # Example date for resolution
    date = "2025-05-23"
    result = resolve_market(date)
    print(result)

if __name__ == "__main__":
    main()