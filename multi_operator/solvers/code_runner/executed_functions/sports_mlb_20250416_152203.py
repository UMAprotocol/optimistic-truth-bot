import os
import requests
from dotenv import load_dotenv
from datetime import datetime
import logging

# Load API key from .env file
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")

# Constants - RESOLUTION MAPPING using team names
RESOLUTION_MAP = {
    "CHC": "p2",  # Chicago Cubs win maps to p2
    "SD": "p1",   # San Diego Padres win maps to p1
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

def fetch_game_data(date):
    """
    Fetches game data for the specified date.

    Args:
        date: Game date in YYYY-MM-DD format

    Returns:
        Game data dictionary or None if not found
    """
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{date}?key={API_KEY}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        games = response.json()

        # Find the specific game - the API returns an array of game objects
        for game in games:
            if game['HomeTeam'] == 'SD' and game['AwayTeam'] == 'CHC':
                return game
            if game['HomeTeam'] == 'CHC' and game['AwayTeam'] == 'SD':
                return game
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        return None

def determine_resolution(game):
    """
    Determines the resolution based on the game's status and outcome.

    Args:
        game: Game data dictionary from the Scores API

    Returns:
        Resolution string (p1, p2, p3, or p4)
    """
    if not game:
        return "p4"

    status = game.get("Status")
    if status in ["Scheduled", "InProgress", "Delayed", "Suspended"]:
        return "p4"
    elif status == "Final":
        home_team = game['HomeTeam']
        away_team = game['AwayTeam']
        home_score = game['HomeTeamRuns']
        away_score = game['AwayTeamRuns']

        if home_score > away_score:
            return RESOLUTION_MAP[home_team]
        elif away_score > home_score:
            return RESOLUTION_MAP[away_team]
    elif status in ["Postponed", "Canceled"]:
        return "p3"

    return "p4"

def main():
    """
    Main function to query MLB game data and determine the resolution.
    """
    date = "2025-04-14"
    game = fetch_game_data(date)
    resolution = determine_resolution(game)
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()