import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
SPORTS_DATA_IO_CBB_API_KEY = os.getenv("SPORTS_DATA_IO_CBB_API_KEY")
SPORTS_DATA_IO_CFB_API_KEY = os.getenv("SPORTS_DATA_IO_CFB_API_KEY")
SPORTS_DATA_IO_MLB_API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
SPORTS_DATA_IO_NBA_API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")
SPORTS_DATA_IO_NFL_API_KEY = os.getenv("SPORTS_DATA_IO_NFL_API_KEY")
SPORTS_DATA_IO_NHL_API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")

# API endpoints
BINANCE_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
SPORTS_DATA_IO_MLB_ENDPOINT = "https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate"

# Headers for Sports Data IO
HEADERS_MLB = {"Ocp-Apim-Subscription-Key": SPORTS_DATA_IO_MLB_API_KEY}

def get_data_from_proxy(url, headers):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error accessing proxy endpoint: {e}")
        return None

def get_data_from_primary(url, headers):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error accessing primary endpoint: {e}")
        return None

def get_mlb_data(date):
    url = f"{SPORTS_DATA_IO_MLB_ENDPOINT}/{date}"
    data = get_data_from_proxy(url, HEADERS_MLB)
    if data is None:
        data = get_data_from_primary(url, HEADERS_MLB)
    return data

def analyze_mlb_data(data):
    if not data:
        return "p4"  # Unable to retrieve data
    # Example analysis logic
    if len(data) == 0:
        return "p3"  # No games found, assume canceled
    # More complex analysis would go here
    return "p1"  # Placeholder for actual outcome based on analysis

if __name__ == "__main__":
    date = "2025-04-23"  # Example date
    mlb_data = get_mlb_data(date)
    recommendation = analyze_mlb_data(mlb_data)
    print(f"recommendation: {recommendation}")