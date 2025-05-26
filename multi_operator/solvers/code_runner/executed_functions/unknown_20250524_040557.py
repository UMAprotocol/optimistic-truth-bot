import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API keys loaded from environment variables
API_KEYS = {
    "binance": os.getenv("BINANCE_API_KEY"),
    "mlb": os.getenv("SPORTS_DATA_IO_MLB_API_KEY"),
    "nba": os.getenv("SPORTS_DATA_IO_NBA_API_KEY"),
    "nfl": os.getenv("SPORTS_DATA_IO_NFL_API_KEY"),
    "nhl": os.getenv("SPORTS_DATA_IO_NHL_API_KEY"),
    "cfb": os.getenv("SPORTS_DATA_IO_CFB_API_KEY"),
    "cbb": os.getenv("SPORTS_DATA_IO_CBB_API_KEY")
}

# API endpoints
API_ENDPOINTS = {
    "binance": {
        "primary": "https://api.binance.com/api/v3",
        "proxy": "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
    },
    "mlb": {
        "primary": "https://api.sportsdata.io/v3/mlb"
    },
    "nba": {
        "primary": "https://api.sportsdata.io/v3/nba"
    },
    "nfl": {
        "primary": "https://api.sportsdata.io/v3/nfl"
    },
    "nhl": {
        "primary": "https://api.sportsdata.io/v3/nhl"
    },
    "cfb": {
        "primary": "https://api.sportsdata.io/v3/cfb"
    },
    "cbb": {
        "primary": "https://api.sportsdata.io/v3/cbb"
    }
}

# Function to make API requests
def make_api_request(api_category, endpoint_type="primary"):
    headers = {"Ocp-Apim-Subscription-Key": API_KEYS[api_category]}
    url = API_ENDPOINTS[api_category].get(endpoint_type)
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if endpoint_type == "primary" and "proxy" in API_ENDPOINTS[api_category]:
            return make_api_request(api_category, "proxy")
        else:
            print(f"Error: {str(e)}")
            return None

# Example usage of the function
if __name__ == "__main__":
    # Example: Fetch MLB data
    mlb_data = make_api_request("mlb")
    if mlb_data:
        print("MLB data fetched successfully.")
    else:
        print("Failed to fetch MLB data.")