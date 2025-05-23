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
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_nhl_game_data(game_date):
    """
    Fetches NHL game data for a specific date.
    """
    primary_url = f"https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/{game_date}?key={NHL_API_KEY}"
    proxy_url = f"https://minimal-ubuntu-production.up.railway.app/sportsdata-io-proxy/nhl/GamesByDate/{game_date}"

    try:
        # Try proxy endpoint first
        response = requests.get(proxy_url, timeout=10)
        response.raise_for_status()
    except (requests.RequestException, requests.Timeout):
        logging.info("Proxy failed, trying primary endpoint")
        # Fallback to primary endpoint if proxy fails
        response = requests.get(primary_url, timeout=10)
        response.raise_for_status()

    return response.json()

def resolve_market(games):
    """
    Resolves the market based on the game data.
    """
    for game in games:
        if game['HomeTeam'] == "EDM" or game['AwayTeam'] == "EDM":
            if game['Status'] == "Final":
                home_score = game['HomeTeamScore']
                away_score = game['AwayTeamScore']
                if home_score > away_score and game['HomeTeam'] == "EDM":
                    return "p2"  # Oilers win
                elif away_score > home_score and game['AwayTeam'] == "EDM":
                    return "p2"  # Oilers win
                else:
                    return "p1"  # Kings win
            elif game['Status'] == "Canceled":
                return "p3"  # Game canceled, resolve 50-50
            elif game['Status'] == "Postponed":
                return "p4"  # Game postponed, too early to resolve
    return "p4"  # No relevant game found or game not yet played

def main():
    game_date = "2025-04-23"
    try:
        games = fetch_nhl_game_data(game_date)
        resolution = resolve_market(games)
        print(f"recommendation: {RESOLUTION_MAP[resolution]}")
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        print("recommendation: p4")  # Default to unresolved if there's an error

if __name__ == "__main__":
    main()