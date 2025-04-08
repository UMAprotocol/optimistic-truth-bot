import os
import requests
from dotenv import load_dotenv
import logging

# Load environment variables
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
    "Minnesota Twins": "p2",  # Minnesota Twins win maps to p2
    "Houston Astros": "p1",  # Houston Astros win maps to p1
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
        if response.status_code == 404:
            logger.warning("No data found for the specified date.")
            return None
        response.raise_for_status()
        games = response.json()

        for game in games:
            if game["HomeTeam"] == home_team and game["AwayTeam"] == away_team:
                return game
        logger.warning("No matching game found.")
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
    if status == "Final":
        home_score = game.get("HomeTeamRuns")
        away_score = game.get("AwayTeamRuns")
        if home_score > away_score:
            return RESOLUTION_MAP["Houston Astros"]
        else:
            return RESOLUTION_MAP["Minnesota Twins"]
    elif status in ["Postponed", "Canceled"]:
        return RESOLUTION_MAP["50-50"]
    else:
        return RESOLUTION_MAP["Too early to resolve"]

def main():
    date = "2025-04-06"
    home_team = "HOU"
    away_team = "MIN"
    game = fetch_game_data(date, home_team, away_team)
    resolution = determine_resolution(game)
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()