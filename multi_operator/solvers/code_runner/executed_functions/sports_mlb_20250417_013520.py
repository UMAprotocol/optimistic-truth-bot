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
    "Kansas City Royals": "p2",  # Kansas City Royals win maps to p2
    "New York Yankees": "p1",   # New York Yankees win maps to p1
    "50-50": "p3",              # Tie or undetermined maps to p3
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
    Fetches game data for the specified date and teams.
    Returns:
        Game data dictionary or None if not found
    """
    date = "2025-04-16"
    team1_name = "Kansas City Royals"
    team2_name = "New York Yankees"
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{date}?key={API_KEY}"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        games = response.json()
        
        for game in games:
            if game['HomeTeam'] == team1_name and game['AwayTeam'] == team2_name:
                return game
            elif game['HomeTeam'] == team2_name and game['AwayTeam'] == team1_name:
                return game
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
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
        return "p4"  # No game data available

    status = game.get("Status")
    if status == "Final":
        home_team = game.get("HomeTeam")
        away_team = game.get("AwayTeam")
        home_score = game.get("HomeTeamRuns")
        away_score = game.get("AwayTeamRuns")
        
        if home_score > away_score:
            return RESOLUTION_MAP.get(home_team, "p3")
        elif away_score > home_score:
            return RESOLUTION_MAP.get(away_team, "p3")
        else:
            return "p3"  # Tie case
    elif status == "Postponed":
        return "p4"  # Market remains open
    elif status == "Canceled":
        return "p3"  # Game canceled entirely, resolve 50-50
    else:
        return "p4"  # Game not completed or other statuses

def main():
    """
    Main function to query MLB game data and determine the resolution.
    """
    game_data = fetch_game_data()
    resolution = determine_resolution(game_data)
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()