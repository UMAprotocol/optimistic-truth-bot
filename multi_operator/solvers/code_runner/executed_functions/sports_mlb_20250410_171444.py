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
    "50-50": "p3",  # Game canceled or no make-up game maps to p3
    "Too early to resolve": "p4",  # Incomplete data maps to p4
}

logger = logging.getLogger(__name__)

def fetch_game_data():
    """
    Fetches game data for the specified NBA game between Miami Heat and Chicago Bulls.

    Returns:
        Game data dictionary or None if not found
    """
    date = "2025-04-09"
    home_team = "MIA"  # Miami Heat abbreviation
    away_team = "CHI"  # Chicago Bulls abbreviation

    logger.info(f"Fetching game data for {away_team} @ {home_team} on {date}")

    # Use the exact format from the API documentation with key as query parameter
    url = f"https://api.sportsdata.io/v3/nba/scores/json/GamesByDate/{date}?key={API_KEY}"

    logger.debug(f"Using API endpoint: {url}")

    try:
        logger.debug("Sending API request")
        response = requests.get(url)

        if response.status_code == 404:
            logger.warning(
                f"No data found for {date}. Please check the date and ensure data is available."
            )
            return None

        response.raise_for_status()
        games = response.json()
        logger.info(f"Retrieved {len(games)} games for {date}")

        # Find the specific game - the API returns an array of game objects
        for game_data in games:
            if (
                game_data.get("HomeTeam") == home_team
                and game_data.get("AwayTeam") == away_team
            ):
                logger.info(f"Found matching game: {away_team} @ {home_team}")
                return game_data

        logger.warning(
            f"No matching game found between {away_team} and {home_team} on {date}."
        )
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
    home_team = game.get("HomeTeam")
    away_team = game.get("AwayTeam")
    home_score = game.get("HomeTeamScore")
    away_score = game.get("AwayTeamScore")

    logger.info(
        f"Game status: {status}, Score: {away_team} {away_score} - {home_team} {home_score}"
    )

    if status == "Final":
        if home_score > away_score:
            logger.info(f"Home team ({home_team}) won, resolving as Heat")
            return RESOLUTION_MAP["Heat"]
        else:
            logger.info(f"Away team ({away_team}) won, resolving as Bulls")
            return RESOLUTION_MAP["Bulls"]
    elif status == "Postponed":
        logger.info("Game was postponed, too early to resolve")
        return RESOLUTION_MAP["Too early to resolve"]
    elif status == "Canceled":
        logger.info("Game was canceled, resolving as 50-50")
        return RESOLUTION_MAP["50-50"]
    else:
        logger.warning(
            f"Unexpected game state: {status}, defaulting to 'Too early to resolve'"
        )
        return RESOLUTION_MAP["Too early to resolve"]

def main():
    game = fetch_game_data()
    resolution = determine_resolution(game)
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()