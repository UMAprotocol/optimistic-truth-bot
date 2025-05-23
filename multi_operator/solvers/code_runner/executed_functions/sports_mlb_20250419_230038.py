import os
import requests
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
MLB_API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")

# Constants
RESOLUTION_MAP = {
    "Seattle Mariners": "p2",
    "Toronto Blue Jays": "p1",
    "50-50": "p3",
    "Too early to resolve": "p4",
}

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_game_result():
    """
    Fetches the result of the MLB game between Seattle Mariners and Toronto Blue Jays.
    """
    date = "2025-04-19"
    primary_url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{date}?key={MLB_API_KEY}"
    proxy_url = f"https://minimal-ubuntu-production.up.railway.app/sportsdata-proxy/mlb/scores/json/GamesByDate/{date}?key={MLB_API_KEY}"

    try:
        # Try fetching via proxy first
        response = requests.get(proxy_url, timeout=10)
        response.raise_for_status()
    except (requests.RequestException, requests.Timeout):
        logging.info("Proxy failed, trying primary endpoint")
        # Fallback to primary endpoint if proxy fails
        response = requests.get(primary_url, timeout=10)
        response.raise_for_status()

    games = response.json()
    for game in games:
        if game['HomeTeam'] == 'TOR' and game['AwayTeam'] == 'SEA':
            if game['Status'] == 'Final':
                home_score = game['HomeTeamRuns']
                away_score = game['AwayTeamRuns']
                if home_score > away_score:
                    return "p1"  # Toronto Blue Jays win
                elif away_score > home_score:
                    return "p2"  # Seattle Mariners win
            elif game['Status'] in ['Postponed', 'Canceled']:
                return "p3"  # Game not completed or canceled
            else:
                return "p4"  # Game not yet completed or other statuses
    return "p4"  # No game found or other cases

def main():
    result = fetch_game_result()
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()