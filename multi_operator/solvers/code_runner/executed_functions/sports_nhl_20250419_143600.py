import os
import requests
from dotenv import load_dotenv
from datetime import datetime
import logging

# Load API key from .env file
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")

# Check if API key is available
if not API_KEY:
    raise ValueError(
        "SPORTS_DATA_IO_NHL_API_KEY not found in environment variables. "
        "Please add it to your .env file."
    )

# Constants - RESOLUTION MAPPING using internal abbreviations
RESOLUTION_MAP = {
    "GT": "p2",  # Gujarat Titans maps to p2
    "DC": "p1",  # Delhi Capitals maps to p1
    "50-50": "p3",  # Canceled or postponed maps to p3
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
    Fetches game data for the specified IPL match.

    Returns:
        Game data dictionary or None if not found
    """
    date = "2025-04-19"
    team1_api = "GT"
    team2_api = "DC"

    # Use the exact format from the API documentation with key as query parameter
    url = f"https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/{date}?key={API_KEY}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        games = response.json()

        # Find the specific game - the API returns an array of game objects
        for game_data in games:
            home_team = game_data.get("HomeTeam")
            away_team = game_data.get("AwayTeam")
            
            # Check if either team matches our search
            if (home_team == team1_api and away_team == team2_api) or (home_team == team2_api and away_team == team1_api):
                return game_data

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
        return RESOLUTION_MAP["Too early to resolve"]

    status = game.get("Status")
    home_score = game.get("HomeTeamScore")
    away_score = game.get("AwayTeamScore")
    home_team = game.get("HomeTeam")
    away_team = game.get("AwayTeam")

    if status in ["Scheduled", "InProgress"]:
        return RESOLUTION_MAP["Too early to resolve"]
    elif status == "Postponed":
        return RESOLUTION_MAP["50-50"]
    elif status == "Canceled":
        return RESOLUTION_MAP["50-50"]
    elif status == "Final":
        if home_score > away_score:
            winner_team = home_team
        else:
            winner_team = away_team

        return RESOLUTION_MAP[winner_team]

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