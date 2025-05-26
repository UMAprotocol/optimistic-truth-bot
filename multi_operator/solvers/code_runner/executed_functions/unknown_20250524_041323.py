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
    url = API_ENDPOINTS[api_category].get(endpoint_type)
    for _ in range(retries):
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if response.status_code in [502, 503, 504] and endpoint_type == "proxy":
                # Retry with primary endpoint if proxy fails
                return make_request(api_category, "primary")
            else:
                print(f"HTTP Error: {e}")
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
    return None

# Main function to process the market resolution
def process_market_resolution():
    start_date = datetime.strptime("2025-05-17 12:00", "%Y-%m-%d %H:%M")
    end_date = datetime.strptime("2025-05-23 23:59", "%Y-%m-%d %H:%M")
    current_date = datetime.now()

    # Check if current date is within the market resolution period
    if start_date <= current_date <= end_date:
        # Example of using the NBA API to fetch data
        data = make_request("NBA")
        if data:
            # Process the data to check for the mention of "Baby"
            # This is a placeholder for the actual logic to check the data
            for item in data:
                if "Baby" in item.get("description", ""):
                    print("recommendation: p2")  # Yes
                    return
        print("recommendation: p1")  # No
    else:
        print("recommendation: p4")  # Too early / in-progress

# Run the main function
if __name__ == "__main__":
    process_market_resolution()