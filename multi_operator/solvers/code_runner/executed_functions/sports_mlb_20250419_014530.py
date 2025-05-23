import os
import requests
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
NBA_API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")

# Constants
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nba"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/nba-proxy"
RESOLUTION_MAP = {
    "Yes": "p2",
    "No": "p1",
    "Unknown": "p3"
}

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_nba_playoff_status(team):
    """
    Fetches the playoff status for the specified NBA team.
    """
    url = f"{PROXY_ENDPOINT}/scores/json/PlayoffTeams/2024?key={NBA_API_KEY}"
    fallback_url = f"{PRIMARY_ENDPOINT}/scores/json/PlayoffTeams/2024?key={NBA_API_KEY}"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except (requests.RequestException, requests.Timeout):
        logging.warning("Proxy failed, falling back to primary endpoint.")
        response = requests.get(fallback_url, timeout=10)
        response.raise_for_status()

    teams = response.json()
    for team_data in teams:
        if team_data['Key'] == team:
            return "Yes"
    return "No"

def main():
    """
    Main function to determine if the Atlanta Hawks make the 2024-25 NBA Playoffs.
    """
    team_key = "ATL"  # NBA abbreviation for Atlanta Hawks
    try:
        playoff_status = fetch_nba_playoff_status(team_key)
        recommendation = RESOLUTION_MAP[playoff_status]
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        recommendation = RESOLUTION_MAP["Unknown"]

    print(f"recommendation: {recommendation}")

if __name__ == "__main__":
    main()