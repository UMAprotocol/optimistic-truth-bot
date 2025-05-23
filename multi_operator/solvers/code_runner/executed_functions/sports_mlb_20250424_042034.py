import os
import requests
from dotenv import load_dotenv
from datetime import datetime
import logging

# Load API key from .env file
load_dotenv()
MLB_API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")

# Constants - RESOLUTION MAPPING using team names
RESOLUTION_MAP = {
    "Milwaukee Brewers": "p2",  # Milwaukee Brewers win maps to p2
    "San Francisco Giants": "p1",  # San Francisco Giants win maps to p1
    "50-50": "p3",  # Canceled or no make-up game maps to p3
    "Too early to resolve": "p4",  # Incomplete data maps to p4
}

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

def fetch_game_data():
    """
    Fetches game data for the specified MLB game.
    
    Returns:
        Game data dictionary or None if not found
    """
    date = "2025-04-23"
    team1_name = "Milwaukee Brewers"
    team2_name = "San Francisco Giants"
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{date}?key={MLB_API_KEY}"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        games = response.json()

        for game in games:
            if game['HomeTeam'] == team1_name and game['AwayTeam'] == team2_name:
                return game
            elif game['HomeTeam'] == team2_name and game['AwayTeam'] == team1_name:
                return game

        logger.info("No matching game found for the specified teams on the given date.")
        return None

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch game data: {e}")
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

    status = game.get("Status")
    if status == "Final":
        home_score = game.get("HomeTeamRuns")
        away_score = game.get("AwayTeamRuns")
        if home_score > away_score:
            return RESOLUTION_MAP[game["HomeTeam"]]
        else:
            return RESOLUTION_MAP[game["AwayTeam"]]
    elif status == "Canceled":
        return "p3"  # Game canceled with no make-up
    elif status == "Postponed":
        return "p4"  # Game postponed, market remains open

    return "p4"  # Default case if none of the above conditions are met

def main():
    """
    Main function to determine the resolution of the MLB game market.
    """
    game_data = fetch_game_data()
    resolution = determine_resolution(game_data)
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()