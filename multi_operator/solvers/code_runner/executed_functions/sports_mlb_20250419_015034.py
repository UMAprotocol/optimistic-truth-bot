import os
import requests
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
NBA_API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")

# Constants
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nba"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
TEAM = "Miami Heat"
SEASON = "2024-25"

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_nba_standings():
    """
    Fetches NBA standings and checks if Miami Heat has made the playoffs.
    """
    url = f"{PRIMARY_ENDPOINT}/scores/json/Standings/{SEASON}?key={NBA_API_KEY}"
    proxy_url = f"{PROXY_ENDPOINT}/nba-proxy?endpoint={url}&api_key={NBA_API_KEY}"

    try:
        # Try proxy endpoint first
        response = requests.get(proxy_url, timeout=10)
        if response.status_code != 200:
            # Fallback to primary endpoint if proxy fails
            response = requests.get(url, timeout=10)
            response.raise_for_status()
        
        standings = response.json()
        for team_data in standings:
            if team_data["Team"] == TEAM and team_data["PlayoffRank"] and int(team_data["PlayoffRank"]) <= 16:
                return True
        return False
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to fetch NBA standings: {e}")
        return None

def main():
    """
    Main function to determine if Miami Heat made the NBA Playoffs.
    """
    result = fetch_nba_standings()
    if result is True:
        print("recommendation: p2")  # Miami Heat made the playoffs
    elif result is False:
        print("recommendation: p1")  # Miami Heat did not make the playoffs
    else:
        print("recommendation: p3")  # Unable to determine

if __name__ == "__main__":
    main()