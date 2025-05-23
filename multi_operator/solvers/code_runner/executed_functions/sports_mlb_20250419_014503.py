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
TEAM = "Atlanta Hawks"
SEASON = "2024-25"

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_nba_standings():
    """
    Fetches NBA standings to determine if the Atlanta Hawks made the playoffs.
    """
    headers = {'Ocp-Apim-Subscription-Key': NBA_API_KEY}
    url = f"{PRIMARY_ENDPOINT}/scores/json/Standings/{SEASON}"
    proxy_url = f"{PROXY_ENDPOINT}/nba-proxy/scores/json/Standings/{SEASON}"

    try:
        # Try proxy endpoint first
        response = requests.get(proxy_url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.RequestException:
        logging.info("Proxy failed, trying primary endpoint.")
        try:
            # Fallback to primary endpoint
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            logging.error(f"Failed to fetch data from primary endpoint: {e}")
            return None

    return response.json()

def check_playoffs(standings):
    """
    Checks if the Atlanta Hawks are in the top 16 teams of the standings.
    """
    for team_data in standings:
        if team_data['Team'] == TEAM:
            if team_data['PlayoffRank'] and int(team_data['PlayoffRank']) <= 16:
                return "p2"  # Hawks made the playoffs
            break
    return "p1"  # Hawks did not make the playoffs

def main():
    standings = fetch_nba_standings()
    if standings is None:
        print("recommendation: p3")  # Unable to determine due to data fetch failure
    else:
        result = check_playoffs(standings)
        print(f"recommendation: {result}")

if __name__ == "__main__":
    main()