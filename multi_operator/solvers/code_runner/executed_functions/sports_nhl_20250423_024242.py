import os
import requests
from dotenv import load_dotenv
from datetime import datetime
import logging

# Load API key from .env file
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")

# Constants - RESOLUTION MAPPING using team abbreviations
RESOLUTION_MAP = {
    "OTT": "p2",  # Ottawa Senators
    "TOR": "p1",  # Toronto Maple Leafs
    "50-50": "p3",  # Tie or undetermined maps to p3
    "Too early to resolve": "p4",  # Incomplete data maps to p4
}

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

logger.addHandler(console_handler)

def fetch_game_data():
    """
    Fetches game data for the specified NHL game between Ottawa Senators and Toronto Maple Leafs.

    Returns:
        Game data dictionary or None if not found
    """
    date = "2025-04-22"
    team1_api = "OTT"
    team2_api = "TOR"
    url = f"https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/{date}?key={API_KEY}"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        games = response.json()

        for game in games:
            if (game['HomeTeam'] == team1_api and game['AwayTeam'] == team2_api) or \
               (game['HomeTeam'] == team2_api and game['AwayTeam'] == team1_api):
                return game
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        return None

def determine_resolution(game):
    """
    Determines the resolution based on the game's status and outcome.

    Args:
        game: Game data dictionary from the NHL API

    Returns:
        Resolution string (p1, p2, p3, or p4)
    """
    if not game:
        return RESOLUTION_MAP["Too early to resolve"]

    status = game.get("Status")
    if status == "Final":
        home_team = game.get("HomeTeam")
        away_team = game.get("AwayTeam")
        home_score = game.get("HomeTeamScore")
        away_score = game.get("AwayTeamScore")

        if home_score > away_score:
            winner = home_team
        else:
            winner = away_team

        if winner == "OTT":
            return RESOLUTION_MAP["OTT"]
        elif winner == "TOR":
            return RESOLUTION_MAP["TOR"]
    elif status == "Postponed":
        return "p4"  # Market remains open
    elif status == "Canceled":
        return RESOLUTION_MAP["50-50"]

    return RESOLUTION_MAP["Too early to resolve"]

def main():
    """
    Main function to query NHL game data and determine the resolution.
    """
    game = fetch_game_data()
    resolution = determine_resolution(game)
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()