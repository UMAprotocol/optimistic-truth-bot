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

def fetch_nba_playoff_status():
    """
    Fetches the current playoff status of the Memphis Grizzlies for the 2024-25 NBA season.
    """
    primary_url = "https://api.sportsdata.io/v3/nba/scores/json/Standings/2025"
    proxy_url = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-nba-proxy"
    headers = {"Ocp-Apim-Subscription-Key": API_KEY}

    try:
        # Try fetching via proxy first
        response = requests.get(proxy_url, headers=headers, timeout=10)
        response.raise_for_status()
    except Exception as e:
        logging.warning(f"Proxy failed with error: {e}. Trying primary endpoint.")
        try:
            response = requests.get(primary_url, headers=headers, timeout=10)
            response.raise_for_status()
        except Exception as e:
            logging.error(f"Primary endpoint also failed with error: {e}.")
            return "Unknown"

    data = response.json()
    # Check if Memphis Grizzlies are in the top 16 teams
    for team_data in data:
        if team_data["Team"] == "Memphis Grizzlies":
            if team_data["PlayoffRank"] and 1 <= team_data["PlayoffRank"] <= 16:
                return "Yes"
            break

    return "No"

def main():
    """
    Main function to determine if the Memphis Grizzlies make the 2024-25 NBA Playoffs.
    """
    result = fetch_nba_playoff_status()
    recommendation = RESOLUTION_MAP.get(result, "p3")
    print(f"recommendation: {recommendation}")

if __name__ == "__main__":
    main()