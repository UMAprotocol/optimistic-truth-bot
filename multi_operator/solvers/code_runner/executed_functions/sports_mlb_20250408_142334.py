import os
import requests
from dotenv import load_dotenv
from datetime import datetime
import logging

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
    "Boston Red Sox": "p2",  # Boston Red Sox win maps to p2
    "St. Louis Cardinals": "p1",  # St. Louis Cardinals win maps to p1
    "50-50": "p3",  # Game canceled or postponed indefinitely maps to p3
    "Too early to resolve": "p4",  # Incomplete data maps to p4
}

logger = logging.getLogger(__name__)

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
    logger.info(f"Fetching game data for {away_team} @ {home_team} on {date}")

    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{date}?key={API_KEY}"
    logger.debug(f"Using API endpoint: {url}")

    try:
        response = requests.get(url)
        response.raise_for_status()
        games = response.json()

        for game_data in games:
            if game_data.get("HomeTeam") == home_team and game_data.get("AwayTeam") == away_team:
                return game_data

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
        return RESOLUTION_MAP["Too early to resolve"]

    status = game.get("Status")
    home_score = game.get("HomeTeamRuns")
    away_score = game.get("AwayTeamRuns")
    home_team = game.get("HomeTeam")
    away_team = game.get("AwayTeam")

    if status == "Final":
        if home_score > away_score:
            return "recommendation: " + RESOLUTION_MAP[home_team]
        elif away_score > home_score:
            return "recommendation: " + RESOLUTION_MAP[away_team]
    elif status in ["Postponed", "Canceled"]:
        return "recommendation: " + RESOLUTION_MAP["50-50"]

    return RESOLUTION_MAP["Too early to resolve"]

def main():
    date = "2025-04-05"
    home_team = "BOS"  # Boston Red Sox
    away_team = "STL"  # St. Louis Cardinals

    game = fetch_game_data(date, home_team, away_team)
    resolution = determine_resolution(game)

    print(resolution)

if __name__ == "__main__":
    main()