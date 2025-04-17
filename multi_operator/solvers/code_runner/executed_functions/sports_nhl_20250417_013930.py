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
    "ANA": "p2",  # Anaheim Ducks maps to p2
    "WPG": "p1",  # Winnipeg Jets maps to p1
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
    url = f"https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/{date}?key={API_KEY}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        games = response.json()
        for game in games:
            if game['HomeTeam'] == 'ANA' and game['AwayTeam'] == 'WPG' or game['HomeTeam'] == 'WPG' and game['AwayTeam'] == 'ANA':
                return game
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch game data: {e}")
        return None

def determine_resolution(game):
    """
    Determines the resolution based on the game's status and outcome.

    Args:
        game: Game data dictionary

    Returns:
        Resolution string (p1, p2, p3, or p4)
    """
    if not game:
        return RESOLUTION_MAP["Too early to resolve"]

    if game['Status'] == 'Final':
        if game['HomeTeam'] == 'ANA' and game['HomeTeamScore'] > game['AwayTeamScore']:
            return RESOLUTION_MAP['ANA']
        elif game['AwayTeam'] == 'ANA' and game['AwayTeamScore'] > game['HomeTeamScore']:
            return RESOLUTION_MAP['ANA']
        elif game['HomeTeam'] == 'WPG' and game['HomeTeamScore'] > game['AwayTeamScore']:
            return RESOLUTION_MAP['WPG']
        elif game['AwayTeam'] == 'WPG' and game['AwayTeamScore'] > game['HomeTeamScore']:
            return RESOLUTION_MAP['WPG']
    elif game['Status'] == 'Canceled':
        return RESOLUTION_MAP['50-50']
    elif game['Status'] == 'Postponed':
        return RESOLUTION_MAP["Too early to resolve"]

    return RESOLUTION_MAP["50-50"]

def main():
    """
    Main function to query NHL game data and determine the resolution.
    """
    date = "2025-04-16"
    game = fetch_game_data(date)
    resolution = determine_resolution(game)
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()