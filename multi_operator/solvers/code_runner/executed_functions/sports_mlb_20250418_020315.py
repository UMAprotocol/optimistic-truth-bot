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
    "New York Yankees": "p2",
    "Tampa Bay Rays": "p1",
    "50-50": "p3",
    "Too early to resolve": "p4",
}

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

def fetch_game_data():
    """
    Fetches game data for the specified MLB game between New York Yankees and Tampa Bay Rays.
    """
    date = "2025-04-17"
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{date}?key={MLB_API_KEY}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        games = response.json()
        for game in games:
            if game['HomeTeam'] == 'NYY' and game['AwayTeam'] == 'TBR' or game['HomeTeam'] == 'TBR' and game['AwayTeam'] == 'NYY':
                return game
        logger.info("No game found for the specified teams on the given date.")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch game data: {e}")
        return None

def determine_resolution(game):
    """
    Determines the resolution based on the game's status and outcome.
    """
    if not game:
        return "p4"  # Too early to resolve or no data

    if game['Status'] == 'Final':
        if game['HomeTeamRuns'] > game['AwayTeamRuns']:
            winner = game['HomeTeam']
        else:
            winner = game['AwayTeam']

        if winner == 'NYY':
            return "p2"  # New York Yankees win
        elif winner == 'TBR':
            return "p1"  # Tampa Bay Rays win
    elif game['Status'] == 'Canceled':
        return "p3"  # Game canceled, resolve 50-50
    elif game['Status'] == 'Postponed':
        return "p4"  # Game postponed, too early to resolve

    return "p4"  # Default case if none of the above conditions are met

def main():
    """
    Main function to determine the resolution of the MLB game.
    """
    game_data = fetch_game_data()
    resolution = determine_resolution(game_data)
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()