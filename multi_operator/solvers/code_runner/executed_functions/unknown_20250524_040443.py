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
    "MLB": {
        "primary": "https://api.sportsdata.io/v3/mlb"
    },
    "NBA": {
        "primary": "https://api.sportsdata.io/v3/nba"
    },
    "NFL": {
        "primary": "https://api.sportsdata.io/v3/nfl"
    },
    "NHL": {
        "primary": "https://api.sportsdata.io/v3/nhl"
    },
    "CFB": {
        "primary": "https://api.sportsdata.io/v3/cfb"
    },
    "CBB": {
        "primary": "https://api.sportsdata.io/v3/cbb"
    }
}

# Function to make API requests
def make_request(api_category, endpoint_type="primary", retries=3):
    headers = {"Ocp-Apim-Subscription-Key": API_KEYS[api_category]}
    url = API_ENDPOINTS[api_category][endpoint_type]
    for _ in range(retries):
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if response.status_code == 429:
                continue  # Retry logic for rate limit errors
            raise e
        except requests.exceptions.RequestException as e:
            if endpoint_type == "primary" and "proxy" in API_ENDPOINTS[api_category]:
                return make_request(api_category, "proxy")  # Fallback to proxy
            raise e

# Main function to check if Trump mentioned "Peace through strength"
def check_trump_statement():
    start_date = datetime(2025, 5, 17, 12, 0)
    end_date = datetime(2025, 5, 23, 23, 59)
    current_time = datetime.now()

    if current_time < start_date:
        return "p4"  # Too early
    if current_time > end_date:
        return "p1"  # No mention found

    # Example of how to use the API (this part is hypothetical and should be replaced with actual logic)
    data = make_request("NBA")
    for item in data:
        if "Peace through strength" in item.get("speech", ""):
            return "p2"  # Yes, mentioned

    return "p1"  # No mention found

# Run the main function and print the recommendation
if __name__ == "__main__":
    result = check_trump_statement()
    print("recommendation:", result)