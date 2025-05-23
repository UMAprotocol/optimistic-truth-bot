import os
import requests
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
NHL_API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")

# Constants
RESOLUTION_MAP = {
    "STL": "p2",  # St. Louis Blues
    "WPG": "p1",  # Winnipeg Jets
    "50-50": "p3",
    "Too early to resolve": "p4",
}

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

def fetch_nhl_game_data(game_date, team1, team2):
    """
    Fetches NHL game data for the specified teams and date.
    """
    primary_url = f"https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/{game_date}?key={NHL_API_KEY}"
    proxy_url = f"https://minimal-ubuntu-production.up.railway.app/sportsdata-io-proxy/nhl/GamesByDate/{game_date}?key={NHL_API_KEY}"
    
    try:
        # Try proxy endpoint first
        response = requests.get(proxy_url, timeout=10)
        response.raise_for_status()
    except requests.RequestException:
        logger.warning("Proxy failed, falling back to primary endpoint.")
        try:
            # Fallback to primary endpoint
            response = requests.get(primary_url, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Failed to fetch data from primary endpoint: {e}")
            return None

    games = response.json()
    for game in games:
        if (game['HomeTeam'] == team1 and game['AwayTeam'] == team2) or (game['HomeTeam'] == team2 and game['AwayTeam'] == team1):
            return game
    return None

def resolve_market(game):
    """
    Resolves the market based on the game data.
    """
    if not game:
        return "p4"  # No game data available

    if game['Status'] == "Canceled":
        return RESOLUTION_MAP["50-50"]
    elif game['Status'] == "Final":
        home_score = game['HomeTeamScore']
        away_score = game['AwayTeamScore']
        if home_score > away_score:
            return RESOLUTION_MAP[game['HomeTeam']]
        elif away_score > home_score:
            return RESOLUTION_MAP[game['AwayTeam']]
    return "p4"  # Game not completed or other statuses

def main():
    game_date = "2025-04-21"
    team1 = "STL"  # St. Louis Blues
    team2 = "WPG"  # Winnipeg Jets

    game = fetch_nhl_game_data(game_date, team1, team2)
    resolution = resolve_market(game)
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()