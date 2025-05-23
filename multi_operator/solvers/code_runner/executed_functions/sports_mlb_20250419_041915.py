import os
import requests
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")

# Constants
RESOLUTION_MAP = {
    "Yes": "p2",
    "No": "p1",
    "Unknown": "p3"
}

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_nba_standings():
    """
    Fetches the current NBA standings to determine if Memphis Grizzlies have made the playoffs.
    """
    primary_url = "https://api.sportsdata.io/v3/nba/scores/json/Standings/2025"
    proxy_url = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-proxy/nba/Standings/2025"
    headers = {"Ocp-Apim-Subscription-Key": API_KEY}

    try:
        # Try fetching data from the proxy endpoint first
        response = requests.get(proxy_url, headers=headers, timeout=10)
        response.raise_for_status()
    except Exception as e:
        logging.warning(f"Proxy failed with error: {e}. Trying primary endpoint.")
        try:
            # Fallback to the primary endpoint if proxy fails
            response = requests.get(primary_url, headers=headers, timeout=10)
            response.raise_for_status()
        except Exception as e:
            logging.error(f"Primary endpoint also failed with error: {e}.")
            return None

    return response.json()

def determine_playoff_status(standings):
    """
    Determines if the Memphis Grizzlies have made the playoffs based on the standings data.
    """
    if not standings:
        return "Unknown"

    for team in standings:
        if team["Team"] == "MEM":
            # Check if the team's position qualifies for playoffs (top 8 in their conference)
            if team["ConferenceRank"] <= 8:
                return "Yes"
            else:
                return "No"

    return "Unknown"

def main():
    standings = fetch_nba_standings()
    playoff_status = determine_playoff_status(standings)
    recommendation = RESOLUTION_MAP.get(playoff_status, "p3")
    print(f"recommendation: {recommendation}")

if __name__ == "__main__":
    main()