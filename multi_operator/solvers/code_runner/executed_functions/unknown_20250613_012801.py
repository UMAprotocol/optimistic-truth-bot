import os
import requests
from datetime import datetime
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

def get_api_response(api_category, endpoint_type="primary"):
    headers = {"Ocp-Apim-Subscription-Key": API_KEYS[api_category]}
    primary_url = API_ENDPOINTS[api_category].get("primary")
    proxy_url = API_ENDPOINTS[api_category].get("proxy")

    try:
        # Try proxy endpoint first if available
        if proxy_url and endpoint_type == "proxy":
            response = requests.get(proxy_url, headers=headers, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                # Fallback to primary if proxy fails
                response = requests.get(primary_url, headers=headers, timeout=10)
                return response.json()
        else:
            # Use primary endpoint
            response = requests.get(primary_url, headers=headers, timeout=10)
            return response.json()
    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")
        return None

def check_military_action():
    # Example of checking for a specific event, modify as needed
    today = datetime.now()
    if today > datetime(2025, 6, 30):
        # Assuming the event is to check for any military action before July 2025
        data = get_api_response("BINANCE")  # Example, replace with actual logic
        if data and "military_action" in data:
            return "recommendation: p2"  # Yes, military action occurred
        else:
            return "recommendation: p1"  # No military action occurred
    else:
        return "recommendation: p4"  # Too early to resolve

if __name__ == "__main__":
    result = check_military_action()
    print(result)