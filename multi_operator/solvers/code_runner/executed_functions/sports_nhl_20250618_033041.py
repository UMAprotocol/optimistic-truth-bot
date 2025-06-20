import os
import requests
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NHL_API_KEY")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# Constants
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nhl"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

def get_data_from_api(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching data from API: {e}")
        return None

def resolve_nhl_winner():
    # Fetch the latest season winner
    season_winner_url = f"{PRIMARY_ENDPOINT}/scores/json/CurrentSeason"
    season_data = get_data_from_api(season_winner_url)
    if season_data:
        current_season = season_data['Season']
        winner_url = f"{PRIMARY_ENDPOINT}/scores/json/Standings/{current_season}"
        standings = get_data_from_api(winner_url)
        if standings:
            # Assuming the API returns standings sorted with the champion at the top
            champion = standings[0]
            if champion['Conference'] == 'Eastern':
                return "recommendation: p2"  # East wins
            elif champion['Conference'] == 'Western':
                return "recommendation: p1"  # West wins
    return "recommendation: p3"  # Unable to determine

if __name__ == "__main__":
    result = resolve_nhl_winner()
    print(result)