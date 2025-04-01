import os
import requests
from dotenv import load_dotenv
from datetime import datetime
import logging

# Load API key from .env file
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")

# Constants
GAME_DATE = "2025-03-30"
HOME_TEAM = "TOR"
AWAY_TEAM = "BAL"
RESOLUTION_MAP = {
    "Blue Jays": "p1",
    "Orioles": "p2",
    "50-50": "p3",
    "Too early to resolve": "p4",
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

    # Use the exact format from the API documentation with key as query parameter
    url = f"https://api.sportsdata.io/v3/mlb/stats/json/BoxScoresFinal/{date}?key={API_KEY}"

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
            game_info = game_data.get("Game", {})
            if (
                game_info.get("HomeTeam") == home_team
                and game_info.get("AwayTeam") == away_team
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
        game: Game data dictionary from the BoxScoresFinal endpoint

    Returns:
        Resolution string (p1, p2, p3, or p4)
    """
    if not game:
        logger.info("No game data available, returning 'Too early to resolve'")
        return RESOLUTION_MAP["Too early to resolve"]

    # Extract game info from the nested structure
    game_info = game.get("Game", {})

    status = game_info.get("Status")
    home_score = game_info.get("HomeTeamRuns")
    away_score = game_info.get("AwayTeamRuns")
    home_team_name = game_info.get("HomeTeam")
    away_team_name = game_info.get("AwayTeam")

    logger.info(
        f"Game status: {status}, Score: {away_team_name} {away_score} - {home_team_name} {home_score}"
    )

    if status in ["Scheduled", "Delayed"]:
        logger.info(f"Game is {status}, too early to resolve")
        return RESOLUTION_MAP["Too early to resolve"]
    elif status in ["Postponed", "Canceled"]:
        logger.info(f"Game was {status}, resolving as 50-50")
        return RESOLUTION_MAP["50-50"]
    elif status == "Suspended":
        current_time = datetime.utcnow()
        deadline = datetime(2025, 4, 2, 3, 59, 59)  # April 1, 11:59 PM UTC
        logger.info(
            f"Game is suspended. Current time: {current_time}, Deadline: {deadline}"
        )

        if current_time <= deadline:
            logger.info("Before deadline, too early to resolve")
            return RESOLUTION_MAP["Too early to resolve"]
        else:
            logger.info("After deadline, resolving as 50-50")
            return RESOLUTION_MAP["50-50"]
    elif status == "Final":
        if home_score is not None and away_score is not None:
            if home_score == away_score:
                logger.info("Game ended in a tie, resolving as 50-50")
                return RESOLUTION_MAP["50-50"]
            elif home_score > away_score:
                logger.info(f"Home team ({home_team_name}) won, resolving as Blue Jays")
                return RESOLUTION_MAP["Blue Jays"]
            else:
                logger.info(f"Away team ({away_team_name}) won, resolving as Orioles")
                return RESOLUTION_MAP["Orioles"]

    logger.warning(
        f"Unexpected game state: {status}, defaulting to 'Too early to resolve'"
    )
    return RESOLUTION_MAP["Too early to resolve"]


def main():
    game = fetch_game_data(GAME_DATE, HOME_TEAM, AWAY_TEAM)
    print(game)
    resolution = determine_resolution(game)
    print(f"recommendation: {resolution}")


if __name__ == "__main__":
    main()
