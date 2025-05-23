import os
import requests
from dotenv import load_dotenv
from datetime import datetime
import logging

# Load API key from .env file
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")

# Constants - RESOLUTION MAPPING using internal abbreviations
RESOLUTION_MAP = {
    "Royal Challengers Bangalore": "p2",  # Maps to p2
    "Rajasthan Royals": "p1",  # Maps to p1
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
    Fetches game data for the specified IPL game.

    Returns:
        Game data dictionary or None if not found
    """
    date = "2025-04-24"
    team1_name = "Royal Challengers Bangalore"
    team2_name = "Rajasthan Royals"
    
    url = f"https://api.sportsdata.io/v3/cricket/scores/json/GamesByDate/{date}?key={API_KEY}"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        games = response.json()

        for game in games:
            if game['HomeTeamName'] == team1_name and game['AwayTeamName'] == team2_name:
                return game
            elif game['HomeTeamName'] == team2_name and game['AwayTeamName'] == team1_name:
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
        return "recommendation: p4"

    status = game.get("Status")
    if status == "Canceled":
        return "recommendation: p3"
    elif status == "Postponed":
        return "recommendation: p4"
    elif status == "Final":
        home_score = game.get("HomeTeamScore")
        away_score = game.get("AwayTeamScore")
        if home_score > away_score:
            return "recommendation: " + RESOLUTION_MAP[game["HomeTeamName"]]
        elif away_score > home_score:
            return "recommendation: " + RESOLUTION_MAP[game["AwayTeamName"]]
        else:
            return "recommendation: p3"
    else:
        return "recommendation: p4"

def main():
    """
    Main function to query IPL game data and determine the resolution.
    """
    game = fetch_game_data()
    resolution = determine_resolution(game)
    print(resolution)

if __name__ == "__main__":
    main()