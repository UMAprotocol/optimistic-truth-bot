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
    "Texas Rangers": "p2",  # Texas Rangers win maps to p2
    "Tampa Bay Rays": "p1",  # Tampa Bay Rays win maps to p1
    "50-50": "p3",  # Game canceled or postponed indefinitely maps to p3
    "Too early to resolve": "p4",  # Incomplete data maps to p4
}

def fetch_game_data(date, home_team, away_team):
    """
    Fetches game data for the specified date and teams.

    Args:
        date: Game date in YYYY-MM-DD format
        home_team: Home team abbreviation
        away_team: Away team abbreviation

    Returns:
        Game data dictionary or None if not found
    """
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{date}?key={API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        games = response.json()
        for game in games:
            if game['HomeTeam'] == home_team and game['AwayTeam'] == away_team:
                return game
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
    if status == "Final":
        home_score = game.get("HomeTeamRuns")
        away_score = game.get("AwayTeamRuns")
        if home_score > away_score:
            return RESOLUTION_MAP["Texas Rangers"]
        else:
            return RESOLUTION_MAP["Tampa Bay Rays"]
    elif status in ["Canceled", "Postponed"]:
        return RESOLUTION_MAP["50-50"]
    else:
        return RESOLUTION_MAP["Too early to resolve"]

def main():
    # Hardcoded values based on the specific question
    date = "2025-04-05"
    home_team = "TEX"  # Texas Rangers
    away_team = "TBR"  # Tampa Bay Rays

    game = fetch_game_data(date, home_team, away_team)
    resolution = determine_resolution(game)
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()