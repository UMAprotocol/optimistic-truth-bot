import os
import requests
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
NHL_API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")

# Constants
RESOLUTION_MAP = {
    "EDM": "p2",  # Edmonton Oilers
    "LAK": "p1",  # Los Angeles Kings
    "50-50": "p3",
    "Too early to resolve": "p4",
}

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

def fetch_nhl_game_data(game_date):
    """
    Fetches NHL game data for a specific date.
    """
    primary_url = f"https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/{game_date}?key={NHL_API_KEY}"
    proxy_url = f"https://minimal-ubuntu-production.up.railway.app/binance-proxy/v3/nhl/scores/json/GamesByDate/{game_date}?key={NHL_API_KEY}"

    try:
        # Try proxy endpoint first
        response = requests.get(proxy_url, timeout=10)
        response.raise_for_status()
    except (requests.RequestException, requests.Timeout):
        logger.warning("Proxy failed, falling back to primary endpoint")
        try:
            # Fallback to primary endpoint
            response = requests.get(primary_url, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Failed to fetch data from primary endpoint: {e}")
            return None

    games = response.json()
    return games

def resolve_market(games):
    """
    Resolves the market based on the game data.
    """
    for game in games:
        if game['HomeTeam'] == 'EDM' or game['AwayTeam'] == 'EDM':
            if game['Status'] == 'Final':
                home_score = game['HomeTeamScore']
                away_score = game['AwayTeamScore']
                if home_score > away_score and game['HomeTeam'] == 'EDM':
                    return "recommendation: " + RESOLUTION_MAP["EDM"]
                elif away_score > home_score and game['AwayTeam'] == 'EDM':
                    return "recommendation: " + RESOLUTION_MAP["EDM"]
                else:
                    return "recommendation: " + RESOLUTION_MAP["LAK"]
            elif game['Status'] == 'Postponed':
                return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]
            elif game['Status'] == 'Canceled':
                return "recommendation: " + RESOLUTION_MAP["50-50"]
    return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

def main():
    """
    Main function to fetch NHL game data and resolve the market.
    """
    game_date = "2025-04-21"
    games = fetch_nhl_game_data(game_date)
    if games:
        result = resolve_market(games)
        print(result)
    else:
        print("recommendation: " + RESOLUTION_MAP["Too early to resolve"])

if __name__ == "__main__":
    main()