import os
import requests
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
NBA_API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")

# Constants
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nba"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-nba-proxy"
TEAM = "Atlanta Hawks"
SEASON = "2024-25"

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

def fetch_nba_standings():
    """
    Fetches NBA standings to determine if the Atlanta Hawks have made the playoffs.
    """
    headers = {'Ocp-Apim-Subscription-Key': NBA_API_KEY}
    url = f"{PROXY_ENDPOINT}/scores/json/Standings/{SEASON}"
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        logger.info("Proxy failed, trying primary endpoint")
        url = f"{PRIMARY_ENDPOINT}/scores/json/Standings/{SEASON}"
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch data from primary endpoint: {e}")
            return None

def check_playoffs(standings):
    """
    Checks if the Atlanta Hawks are in the top 16 teams of the standings.
    """
    if standings is None:
        return "p3"  # Unknown/50-50 if data is not available

    # Filter for the Eastern and Western conference teams in the playoffs
    playoff_teams = [team for team in standings if team['ConferenceRank'] <= 8]
    hawks = [team for team in playoff_teams if team['Team'] == TEAM]

    if hawks:
        return "p2"  # Yes, Hawks are in the playoffs
    else:
        return "p1"  # No, Hawks did not make the playoffs

def main():
    standings = fetch_nba_standings()
    result = check_playoffs(standings)
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()