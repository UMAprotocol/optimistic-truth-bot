import os
import requests
from dotenv import load_dotenv
from datetime import datetime

# Load API key from .env file
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")

# Check if API key is available
if not API_KEY:
    raise ValueError(
        "SPORTS_DATA_IO_MLB_API_KEY not found in environment variables. "
        "Please add it to your .env file."
    )

# Constants - RESOLUTION MAPPING
RESOLUTION_MAP = {
    "Hurricanes": "p2",  # Hurricanes win maps to p2
    "Capitals": "p1",    # Capitals win maps to p1
    "50-50": "p3",       # Game canceled or postponed without resolution maps to p3
    "Too early to resolve": "p4",  # Incomplete data maps to p4
}

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
        response = requests.get(url)
        response.raise_for_status()
        games = response.json()

        # Find the specific game - the API returns an array of game objects
        for game_data in games:
            if (game_data.get("HomeTeam") == "CAR" and game_data.get("AwayTeam") == "WAS") or \
               (game_data.get("HomeTeam") == "WAS" and game_data.get("AwayTeam") == "CAR"):
                return game_data
        return None

    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")
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

    status = game.get("Status")
    home_team = game.get("HomeTeam")
    away_team = game.get("AwayTeam")
    home_score = game.get("HomeTeamScore")
    away_score = game.get("AwayTeamScore")

    if status == "Final":
        if home_team == "CAR" and home_score > away_score:
            return RESOLUTION_MAP["Hurricanes"]
        elif away_team == "CAR" and away_score > home_score:
            return RESOLUTION_MAP["Hurricanes"]
        elif home_team == "WAS" and home_score > away_score:
            return RESOLUTION_MAP["Capitals"]
        elif away_team == "WAS" and away_score > home_score:
            return RESOLUTION_MAP["Capitals"]
    elif status in ["Postponed", "Canceled"]:
        return RESOLUTION_MAP["50-50"]

    return RESOLUTION_MAP["Too early to resolve"]

def main():
    game_date = "2025-04-10"
    game = fetch_game_data(game_date)
    resolution = determine_resolution(game)
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()