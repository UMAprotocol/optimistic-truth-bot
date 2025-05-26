import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API keys loaded from environment variables
API_KEYS = {
    "MLB": os.getenv("SPORTS_DATA_IO_MLB_API_KEY"),
    "NBA": os.getenv("SPORTS_DATA_IO_NBA_API_KEY"),
    "NFL": os.getenv("SPORTS_DATA_IO_NFL_API_KEY"),
    "NHL": os.getenv("SPORTS_DATA_IO_NHL_API_KEY"),
    "CFB": os.getenv("SPORTS_DATA_IO_CFB_API_KEY"),
    "CBB": os.getenv("SPORTS_DATA_IO_CBB_API_KEY"),
    "BINANCE": os.getenv("BINANCE_API_KEY")
}

# API endpoints
API_ENDPOINTS = {
    "MLB": "https://api.sportsdata.io/v3/mlb/scores/json",
    "NBA": "https://api.sportsdata.io/v3/nba/scores/json",
    "NFL": "https://api.sportsdata.io/v3/nfl/scores/json",
    "NHL": "https://api.sportsdata.io/v3/nhl/scores/json",
    "CFB": "https://api.sportsdata.io/v3/cfb/scores/json",
    "CBB": "https://api.sportsdata.io/v3/cbb/scores/json",
    "BINANCE": "https://api.binance.com/api/v3"
}

# Proxy endpoints
PROXY_ENDPOINTS = {
    "BINANCE": "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
}

# Headers for requests
HEADERS = {
    "MLB": {"Ocp-Apim-Subscription-Key": API_KEYS["MLB"]},
    "NBA": {"Ocp-Apim-Subscription-Key": API_KEYS["NBA"]},
    "NFL": {"Ocp-Apim-Subscription-Key": API_KEYS["NFL"]},
    "NHL": {"Ocp-Apim-Subscription-Key": API_KEYS["NHL"]},
    "CFB": {"Ocp-Apim-Subscription-Key": API_KEYS["CFB"]},
    "CBB": {"Ocp-Apim-Subscription-Key": API_KEYS["CBB"]},
    "BINANCE": {"X-MBX-APIKEY": API_KEYS["BINANCE"]}
}

def get_data(api_category, endpoint, params=None):
    url = API_ENDPOINTS[api_category] + endpoint
    proxy_url = PROXY_ENDPOINTS.get(api_category)
    headers = HEADERS[api_category]

    try:
        response = requests.get(proxy_url if proxy_url else url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if proxy_url:
            # Fallback to primary endpoint if proxy fails
            try:
                response = requests.get(url, headers=headers, params=params, timeout=10)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException:
                return None
        return None

# Example usage
if __name__ == "__main__":
    # Example: Get MLB teams
    teams_data = get_data("MLB", "/Teams")
    if teams_data:
        print("Teams data retrieved successfully.")
    else:
        print("Failed to retrieve teams data.")