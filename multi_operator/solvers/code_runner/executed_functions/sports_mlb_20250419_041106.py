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
TEAM = "Dallas Mavericks"
SEASON = "2024-25"

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

def fetch_nba_standings():
    """
    Fetches the NBA standings to determine if the Dallas Mavericks have made the playoffs.
    """
    url = f"{PRIMARY_ENDPOINT}/scores/json/Standings/{SEASON}?key={NBA_API_KEY}"
    proxy_url = f"{PROXY_ENDPOINT}/scores/json/Standings/{SEASON}?key={NBA_API_KEY}"

    try:
        # Try fetching via proxy first
        response = requests.get(proxy_url, timeout=10)
        response.raise_for_status()
    except (requests.RequestException, requests.Timeout):
        logger.info("Proxy failed, trying primary endpoint")
        try:
            # Fallback to primary endpoint if proxy fails
            response = requests.get(url, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Failed to fetch data from primary endpoint: {e}")
            return None

    return response.json()

def check_playoffs(standings):
    """
    Checks if the Dallas Mavericks are in the top 16 teams of the standings.
    """
    if standings is None:
        return "p4"  # Unable to resolve due to data fetch failure

    for team_data in standings:
        if team_data["Team"] == TEAM:
            if team_data["PlayoffRank"] and int(team_data["PlayoffRank"]) <= 16:
                return "p2"  # Mavericks made the playoffs
            break

    return "p1"  # Mavericks did not make the playoffs or data not found

def main():
    standings = fetch_nba_standings()
    result = check_playoffs(standings)
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()