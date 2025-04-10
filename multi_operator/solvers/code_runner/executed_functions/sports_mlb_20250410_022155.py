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
    "Heat": "p2",  # Miami Heat win maps to p2
    "Bulls": "p1",  # Chicago Bulls win maps to p1
    "50-50": "p3",  # Canceled or no make-up game maps to p3
    "Too early to resolve": "p4",  # Incomplete data maps to p4
}

logger = logging.getLogger(__name__)

def fetch_game_data():
    """
    Fetches game data for the Miami Heat vs. Chicago Bulls game scheduled for April 9, 2025.

    Returns:
        Game data dictionary or None if not found
    """
    date = "2025-04-09"
    home_team = "MIA"
    away_team = "CHI"
    logger.info(f"Fetching game data for {away_team} @ {home_team} on {date}")

    url = f"https://api.sportsdata.io/v3/nba/scores/json/GamesByDate/{date}?key={API_KEY}"
    logger.debug(f"Using API endpoint: {url}")

    try:
        logger.debug("Sending API request")
        response = requests.get(url)
        response.raise_for_status()
        games = response.json()
        logger.info(f"Retrieved {len(games)} games for {date}")

        for game_data in games:
            if game_data.get("HomeTeam") == home_team and game_data.get("AwayTeam") == away_team:
                logger.info(f"Found matching game: {away_team} @ {home_team}")
                return game_data

        logger.warning(f"No matching game found between {away_team} and {home_team} on {date}.")
        return None

    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        return None
    except ValueError as e:
        logger.error(f"Failed to parse API response: {e}")
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
        logger.info("No game data available, returning 'Too early to resolve'")
        return RESOLUTION_MAP["Too early to resolve"]

    status = game.get("Status")
    home_team_score = game.get("HomeTeamScore")
    away_team_score = game.get("AwayTeamScore")

    logger.info(f"Game status: {status}, Score: MIA {home_team_score} - CHI {away_team_score}")

    if status == "Final":
        if home_team_score > away_team_score:
            return RESOLUTION_MAP["Heat"]
        elif away_team_score > home_team_score:
            return RESOLUTION_MAP["Bulls"]
    elif status == "Canceled":
        return RESOLUTION_MAP["50-50"]
    elif status == "Postponed":
        return RESOLUTION_MAP["Too early to resolve"]

    return RESOLUTION_MAP["Too early to resolve"]

def main():
    game = fetch_game_data()
    resolution = determine_resolution(game)
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()