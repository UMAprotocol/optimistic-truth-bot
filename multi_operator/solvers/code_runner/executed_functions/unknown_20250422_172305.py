import os
import requests
from dotenv import load_dotenv
import logging
import re

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")

# Constants
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nba"

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

def fetch_video_data():
    """
    Fetches video data from the NBA API and checks for the term "Trump Effect".
    """
    headers = {"Ocp-Apim-Subscription-Key": API_KEY}
    url = f"{PROXY_ENDPOINT}/stats/json/GamesByDate/2025-12-31"
    
    try:
        # Try fetching through proxy endpoint
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch data through proxy: {e}. Trying primary endpoint.")
        try:
            # Fallback to primary endpoint
            url = f"{PRIMARY_ENDPOINT}/stats/json/GamesByDate/2025-12-31"
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch data through primary endpoint: {e}")
            return None

    games = response.json()
    for game in games:
        if "Trump Effect" in game.get("Summary", ""):
            return True
    return False

def main():
    """
    Main function to determine if the term "Trump Effect" was mentioned in any NBA game summaries.
    """
    found = fetch_video_data()
    if found:
        print("recommendation: p2")  # Yes
    else:
        print("recommendation: p1")  # No

if __name__ == "__main__":
    main()