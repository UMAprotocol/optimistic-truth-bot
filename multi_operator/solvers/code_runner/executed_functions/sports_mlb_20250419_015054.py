import os
import requests
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
NBA_API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")

# Constants
RESOLUTION_MAP = {
    "Yes": "p2",  # Team makes the playoffs
    "No": "p1",   # Team does not make the playoffs
    "Unknown": "p3"  # Unknown or undetermined
}

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_nba_standings():
    """
    Fetches the current NBA standings and checks if Miami Heat is in the top 16 teams.
    """
    primary_url = f"https://api.sportsdata.io/v3/nba/scores/json/Standings/2025?key={NBA_API_KEY}"
    proxy_url = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-proxy/nba/Standings/2025"

    try:
        # Try proxy endpoint first
        response = requests.get(proxy_url, timeout=10)
        response.raise_for_status()
    except (requests.RequestException, requests.Timeout):
        logging.info("Proxy failed, trying primary endpoint.")
        # Fallback to primary endpoint if proxy fails
        response = requests.get(primary_url, timeout=10)
        response.raise_for_status()

    standings = response.json()
    # Check if Miami Heat is in the top 16
    playoff_teams = [team for team in standings if team['PlayoffRank'] <= 16 and team['Season'] == 2025]

    for team in playoff_teams:
        if team['Key'] == "MIA":
            return "Yes"
    return "No"

def main():
    """
    Main function to determine if Miami Heat makes the NBA Playoffs.
    """
    try:
        result = fetch_nba_standings()
        recommendation = RESOLUTION_MAP[result]
        print(f"recommendation: {recommendation}")
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        print("recommendation: p3")  # Resolve as unknown if there's an error

if __name__ == "__main__":
    main()