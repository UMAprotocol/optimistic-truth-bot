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
    proxy_url = "https://minimal-ubuntu-production.up.railway.app/sportsdata-proxy/nba/standings/2025"
    headers = {"Ocp-Apim-Subscription-Key": API_KEY}

    try:
        # Try fetching via proxy first
        response = requests.get(proxy_url, headers=headers, timeout=10)
        response.raise_for_status()
    except Exception as e:
        logging.warning(f"Proxy failed with error: {e}. Trying primary endpoint.")
        try:
            # Fallback to primary endpoint if proxy fails
            response = requests.get(primary_url, headers=headers, timeout=10)
            response.raise_for_status()
        except Exception as e:
            logging.error(f"Primary endpoint failed with error: {e}. Unable to fetch data.")
            return None

    return response.json()

def check_playoffs_eligibility(standings):
    """
    Checks if Memphis Grizzlies are in the top 8 of their conference standings.
    """
    if not standings:
        return "Unknown"

    for record in standings:
        if record["Team"] == "MEM" and record["ConferenceRank"] <= 8:
            return "Yes"

    return "No"

def main():
    standings = fetch_nba_standings()
    result = check_playoffs_eligibility(standings)
    recommendation = RESOLUTION_MAP.get(result, "p3")
    print(f"recommendation: {recommendation}")

if __name__ == "__main__":
    main()