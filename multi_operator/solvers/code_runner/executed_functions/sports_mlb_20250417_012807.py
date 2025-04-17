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
    "Boston Red Sox": "p2",  # Boston Red Sox win maps to p2
    "Tampa Bay Rays": "p1",  # Tampa Bay Rays win maps to p1
    "50-50": "p3",  # Tie or undetermined maps to p3
    "Too early to resolve": "p4",  # Incomplete data maps to p4
}

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

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
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        games = response.json()

        for game in games:
            if game['HomeTeam'] == 'BOS' and game['AwayTeam'] == 'TBR':
                return game
            elif game['HomeTeam'] == 'TBR' and game['AwayTeam'] == 'BOS':
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
        return "p4"  # Too early to resolve

    if game['Status'] == 'Final':
        if game['HomeTeamRuns'] > game['AwayTeamRuns']:
            winner = game['HomeTeam']
        else:
            winner = game['AwayTeam']

        if winner == 'BOS':
            return "p2"  # Boston Red Sox win
        elif winner == 'TBR':
            return "p1"  # Tampa Bay Rays win
    elif game['Status'] in ['Postponed', 'Canceled']:
        return "p3"  # Game postponed or canceled, resolve as 50-50

    return "p4"  # Too early to resolve or other statuses

def main():
    """
    Main function to query MLB game data and determine the resolution.
    """
    date = "2025-04-16"  # Date of the game
    game = fetch_game_data(date)
    resolution = determine_resolution(game)
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()