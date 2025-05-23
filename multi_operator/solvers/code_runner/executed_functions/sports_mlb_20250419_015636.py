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
    "Cleveland Guardians": "p2",  # Guardians win maps to p2
    "Pittsburgh Pirates": "p1",   # Pirates win maps to p1
    "50-50": "p3",                # Canceled or no make-up game maps to p3
    "Too early to resolve": "p4", # Incomplete data maps to p4
}

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

def fetch_game_data():
    """
    Fetches game data for the specified MLB game between Cleveland Guardians and Pittsburgh Pirates.
    
    Returns:
        Game data dictionary or None if not found
    """
    date = "2025-04-18"
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{date}?key={MLB_API_KEY}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        games = response.json()
        for game in games:
            if game['HomeTeam'] == 'CLE' and game['AwayTeam'] == 'PIT':
                return game
            elif game['HomeTeam'] == 'PIT' and game['AwayTeam'] == 'CLE':
                return game
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        return None

def determine_resolution(game):
    """
    Determines the resolution based on the game's status and outcome.

    Args:
        game: Game data dictionary from the API

    Returns:
        Resolution string (p1, p2, p3, or p4)
    """
    if not game:
        return "p4"  # No game data available

    status = game['Status']
    if status == "Final":
        if game['HomeTeamRuns'] > game['AwayTeamRuns']:
            winner = game['HomeTeam']
        else:
            winner = game['AwayTeam']
        
        if winner == 'CLE':
            return "p2"  # Cleveland Guardians win
        elif winner == 'PIT':
            return "p1"  # Pittsburgh Pirates win
    elif status == "Canceled":
        return "p3"  # Game canceled with no make-up
    elif status == "Postponed":
        return "p4"  # Game postponed, resolution pending

    return "p4"  # Default to unresolved

def main():
    """
    Main function to determine the resolution of the MLB game between Cleveland Guardians and Pittsburgh Pirates.
    """
    game_data = fetch_game_data()
    resolution = determine_resolution(game_data)
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()