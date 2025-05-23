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
    "Kolkata Knight Riders": "p2",  # Kolkata Knight Riders win maps to p2
    "Gujarat Titans": "p1",  # Gujarat Titans win maps to p1
    "50-50": "p3",  # Canceled or no make-up game maps to p3
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
    # Hardcoded values for demonstration
    date = "2025-04-21"
    team1_name = "Kolkata Knight Riders"
    team2_name = "Gujarat Titans"

    # Use the exact format from the API documentation with key as query parameter
    url = f"https://api.sportsdata.io/v3/mlb/stats/json/BoxScoresFinal/{date}?key={API_KEY}"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        games = response.json()

        # Find the specific game - the API returns an array of game objects
        for game_data in games:
            game_info = game_data.get("Game", {})
            home_team = game_info.get("HomeTeam")
            away_team = game_info.get("AwayTeam")
            
            # Check if either team matches our search
            if home_team in [team1_name, team2_name] and away_team in [team1_name, team2_name]:
                return game_data

        return None

    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        return None

def determine_resolution(game):
    """
    Determines the resolution based on the game's status and outcome.

    Args:
        game: Game data dictionary from the BoxScoresFinal endpoint

    Returns:
        Resolution string (p1, p2, p3, or p4)
    """
    if not game:
        return RESOLUTION_MAP["Too early to resolve"]

    # Extract game info from the nested structure
    game_info = game.get("Game", {})
    status = game_info.get("Status")
    home_team = game_info.get("HomeTeam")
    away_team = game_info.get("AwayTeam")
    home_score = game_info.get("HomeTeamRuns")
    away_score = game_info.get("AwayTeamRuns")

    if status == "Final":
        if home_score > away_score:
            winner = home_team
        else:
            winner = away_team

        return RESOLUTION_MAP.get(winner, "p4")
    elif status in ["Postponed", "Suspended"]:
        return "p4"
    elif status == "Canceled":
        return RESOLUTION_MAP["50-50"]
    else:
        return RESOLUTION_MAP["Too early to resolve"]

def main():
    """
    Main function to query IPL game data and determine the resolution.
    """
    game = fetch_game_data()
    resolution = determine_resolution(game)
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()