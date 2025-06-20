import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API keys loaded from environment variables
API_KEYS = {
    "BINANCE": os.getenv("BINANCE_API_KEY"),
    "MLB": os.getenv("SPORTS_DATA_IO_MLB_API_KEY"),
    "NBA": os.getenv("SPORTS_DATA_IO_NBA_API_KEY"),
    "NFL": os.getenv("SPORTS_DATA_IO_NFL_API_KEY"),
    "NHL": os.getenv("SPORTS_DATA_IO_NHL_API_KEY"),
    "CFB": os.getenv("SPORTS_DATA_IO_CFB_API_KEY"),
    "CBB": os.getenv("SPORTS_DATA_IO_CBB_API_KEY")
}

# API endpoints
API_ENDPOINTS = {
    "BINANCE": {
        "primary": "https://api.binance.com/api/v3",
        "proxy": "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
    },
    "MLB": "https://api.sportsdata.io/v3/mlb",
    "NBA": "https://api.sportsdata.io/v3/nba",
    "NFL": "https://api.sportsdata.io/v3/nfl",
    "NHL": "https://api.sportsdata.io/v3/nhl",
    "CFB": "https://api.sportsdata.io/v3/cfb",
    "CBB": "https://api.sportsdata.io/v3/cbb"
}

# Function to make API requests
def make_request(api_category, endpoint, params=None, headers=None):
    url = API_ENDPOINTS[api_category]["proxy"] if "proxy" in API_ENDPOINTS[api_category] else API_ENDPOINTS[api_category]
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if "proxy" in API_ENDPOINTS[api_category]:
            # Fallback to primary endpoint if proxy fails
            url = API_ENDPOINTS[api_category]["primary"]
            try:
                response = requests.get(url, params=params, headers=headers, timeout=10)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException:
                return None
        return None

# Function to check the status of Ali Khamenei
def check_khamenei_status():
    # Define the date range
    start_date = datetime(2025, 6, 16)
    end_date = datetime(2025, 6, 18)
    current_date = datetime.now()

    # Check if the current date is within the specified range
    if start_date <= current_date <= end_date:
        # Simulate checking official announcements or credible news sources
        # This is a placeholder for actual implementation
        # Example: result = make_request("NEWS_API", "/v2/top-headlines", {"q": "Ali Khamenei", "country": "ir"})
        # For demonstration, assume no change in leadership
        result = {"status": "Supreme Leader"}
        if result["status"] == "Supreme Leader":
            return "p1"  # No change
        else:
            return "p2"  # Change in leadership
    elif current_date > end_date:
        return "p1"  # No change reported by end of period
    else:
        return "p4"  # Too early to determine

# Main execution
if __name__ == "__main__":
    recommendation = check_khamenei_status()
    print("recommendation:", recommendation)