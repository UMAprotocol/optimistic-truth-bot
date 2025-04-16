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

# Constants - RESOLUTION MAPPING using team names
RESOLUTION_MAP = {
    "Athletics": "p2",  # Athletics win maps to p2
    "Chicago White Sox": "p1",  # Chicago White Sox win maps to p1
    "50-50": "p3",  # Tie or undetermined maps to p3
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

def fetch_game_data(date):
    """
    Fetches game data for the specified date.

    Args:
        date: Game date in YYYY-MM-DD format

    Returns:
        Game data dictionary or None if not found
    """
    logger.info(f"Fetching game data for date {date}")
    
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{date}?key={API_KEY}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        games = response.json()
        logger.info(f"Retrieved {len(games)} games for {date}")

        # Find the specific game - the API returns an array of game objects
        for game_data in games:
            if (game_data['HomeTeam'] == "CWS" and game_data['AwayTeam'] == "OAK") or (game_data['HomeTeam'] == "OAK" and game_data['AwayTeam'] == "CWS"):
                logger.info(f"Found matching game: {game_data['AwayTeam']} @ {game_data['HomeTeam']}")
                return game_data

        logger.warning("No matching game found for Athletics vs. Chicago White Sox on the specified date.")
        return None

    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        return None

def determine_resolution(game):
    """
    Determines the resolution based on the game's status and outcome.

    Args:
        game: Game data dictionary from the GamesByDate endpoint

    Returns:
        Resolution string (p1, p2, p3, or p4)
    """
    if not game:
        logger.info("No game data available, returning 'Too early to resolve'")
        return "recommendation: p4"

    status = game.get("Status")
    home_team = game.get("HomeTeam")
    away_team = game.get("AwayTeam")
    home_score = game.get("HomeTeamRuns")
    away_score = game.get("AwayTeamRuns")

    logger.info(f"Game status: {status}, Score: {away_team} {away_score} - {home_team} {home_score}")

    if status == "Final":
        if home_score > away_score:
            winner = home_team
        else:
            winner = away_team

        if winner == "OAK":
            return "recommendation: p2"
        elif winner == "CWS":
            return "recommendation: p1"
    elif status in ["Postponed", "Canceled"]:
        return "recommendation: p3"
    else:
        return "recommendation: p4"

def main():
    """
    Main function to query MLB game data and determine the resolution.
    """
    date = "2025-04-15"
    game = fetch_game_data(date)
    resolution = determine_resolution(game)
    print(resolution)

if __name__ == "__main__":
    main()