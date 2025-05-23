import os
import requests
from dotenv import load_dotenv
from datetime import datetime
import logging

# Load API key from .env file
load_dotenv()
MLB_API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")

# Constants for resolution mapping
RESOLUTION_MAP = {
    "SEA": "p2",  # Seattle Mariners win
    "TOR": "p1",  # Toronto Blue Jays win
    "50-50": "p3",  # Game canceled or postponed without resolution
    "Too early to resolve": "p4",  # Game not yet played or no data available
}

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_game_data():
    """
    Fetches game data for the specified date and teams.
    """
    date = datetime.now().strftime("%Y-%m-%d")
    url_proxy = f"https://minimal-ubuntu-production.up.railway.app/binance-proxy/mlb/scores/json/GamesByDate/{date}"
    url_primary = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{date}?key={MLB_API_KEY}"

    try:
        # Try proxy endpoint first
        response = requests.get(url_proxy, timeout=10)
        if response.status_code != 200:
            # Fallback to primary endpoint if proxy fails
            response = requests.get(url_primary, timeout=10)
        response.raise_for_status()
        games = response.json()

        # Find the game between Seattle Mariners and Toronto Blue Jays
        for game in games:
            if (game['HomeTeam'] == "TOR" and game['AwayTeam'] == "SEA") or (game['HomeTeam'] == "SEA" and game['AwayTeam'] == "TOR"):
                return game
        return None
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to fetch game data: {e}")
        return None

def determine_resolution(game):
    """
    Determines the resolution based on the game's status and outcome.
    """
    if not game:
        return "p4"  # No game data available

    if game['Status'] == "Final":
        if game['HomeTeamRuns'] > game['AwayTeamRuns']:
            winner = game['HomeTeam']
        else:
            winner = game['AwayTeam']

        if winner == "SEA":
            return "p2"  # Seattle Mariners win
        elif winner == "TOR":
            return "p1"  # Toronto Blue Jays win
    elif game['Status'] in ["Canceled", "Postponed"]:
        return "p3"  # Game canceled or postponed

    return "p4"  # Game not final or no clear outcome

def main():
    """
    Main function to query MLB game data and determine the resolution.
    """
    game = fetch_game_data()
    resolution = determine_resolution(game)
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()