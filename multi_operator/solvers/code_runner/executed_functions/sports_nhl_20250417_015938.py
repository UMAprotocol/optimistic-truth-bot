import os
import requests
from dotenv import load_dotenv
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

# Constants - RESOLUTION MAPPING using team abbreviations
RESOLUTION_MAP = {
    "MIA": "p2",  # Miami Heat maps to p2
    "CHI": "p1",  # Chicago Bulls maps to p1
    "50-50": "p3",  # Canceled or postponed game maps to p3
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

def fetch_game_data(date, team1_abbr, team2_abbr):
    """
    Fetches game data for the specified date and teams.

    Args:
        date: Game date in YYYY-MM-DD format
        team1_abbr: Abbreviation of the first team
        team2_abbr: Abbreviation of the second team

    Returns:
        Game data dictionary or None if not found
    """
    logger.info(f"Fetching game data for game between {team1_abbr} and {team2_abbr} on {date}")

    url = f"https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/{date}?key={API_KEY}"
    logger.debug(f"Using API endpoint: {url}")

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        games = response.json()

        for game in games:
            if game['HomeTeam'] == team1_abbr and game['AwayTeam'] == team2_abbr:
                return game
            elif game['HomeTeam'] == team2_abbr and game['AwayTeam'] == team1_abbr:
                return game

        logger.warning(f"No matching game found between {team1_abbr} and {team2_abbr} on {date}.")
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
        logger.info("No game data available, returning 'Too early to resolve'")
        return RESOLUTION_MAP["Too early to resolve"]

    status = game.get("Status")
    home_team = game.get("HomeTeam")
    away_team = game.get("AwayTeam")
    home_score = game.get("HomeScore")
    away_score = game.get("AwayScore")

    logger.info(f"Game status: {status}, Score: {home_team} {home_score} - {away_team} {away_score}")

    if status == "Final":
        if home_score > away_score:
            winner = home_team
        else:
            winner = away_team

        return RESOLUTION_MAP.get(winner, "p4")
    elif status in ["Postponed", "Canceled"]:
        return RESOLUTION_MAP["50-50"]
    else:
        return RESOLUTION_MAP["Too early to resolve"]

def main():
    """
    Main function to query NBA game data and determine the resolution.
    """
    date = "2025-04-16"
    team1_abbr = "MIA"
    team2_abbr = "CHI"

    game = fetch_game_data(date, team1_abbr, team2_abbr)
    resolution = determine_resolution(game)

    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()