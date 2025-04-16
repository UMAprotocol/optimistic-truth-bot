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

# Constants - RESOLUTION MAPPING using internal abbreviations
RESOLUTION_MAP = {
    "Punjab Kings": "p2",  # Punjab Kings win maps to p2
    "Kolkata Knight Riders": "p1",  # Kolkata Knight Riders win maps to p1
    "50-50": "p3",  # Canceled or undetermined maps to p3
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

def fetch_game_data(date, team1_name, team2_name):
    """
    Fetches game data for the specified date and teams.

    Args:
        date: Game date in YYYY-MM-DD format
        team1_name: First team name
        team2_name: Second team name

    Returns:
        Game data dictionary or None if not found
    """
    logger.info(f"Fetching game data for game between {team1_name} and {team2_name} on {date}")

    # Use the exact format from the API documentation with key as query parameter
    url = f"https://api.sportsdata.io/v3/cricket/scores/json/GamesByDate/{date}?key={API_KEY}"
    
    try:
        logger.debug("Sending API request")
        response = requests.get(url)
        response.raise_for_status()
        games = response.json()
        logger.info(f"Retrieved {len(games)} games for {date}")

        # Find the specific game - the API returns an array of game objects
        for game_data in games:
            if game_data['HomeTeamName'] == team1_name and game_data['AwayTeamName'] == team2_name:
                logger.info(f"Found matching game: {team1_name} vs {team2_name}")
                return game_data

        logger.warning(f"No matching game found between {team1_name} and {team2_name} on {date}.")
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
        return "recommendation: p4"

    status = game.get("Status")
    home_team = game.get("HomeTeamName")
    away_team = game.get("AwayTeamName")
    home_score = game.get("HomeTeamScore")
    away_score = game.get("AwayTeamScore")

    logger.info(f"Game status: {status}, Score: {home_team} {home_score} - {away_team} {away_score}")

    if status == "Final":
        if home_score > away_score:
            return f"recommendation: {RESOLUTION_MAP[home_team]}"
        elif away_score > home_score:
            return f"recommendation: {RESOLUTION_MAP[away_team]}"
        else:
            return "recommendation: p3"
    elif status in ["Postponed", "Canceled"]:
        return "recommendation: p3"
    else:
        return "recommendation: p4"

def main():
    """
    Main function to query IPL game data and determine the resolution.
    """
    date = "2025-04-15"
    team1_name = "Punjab Kings"
    team2_name = "Kolkata Knight Riders"
    
    # Fetch game data
    game = fetch_game_data(date, team1_name, team2_name)
    
    # Determine resolution
    resolution = determine_resolution(game)
    
    # Output the recommendation
    print(resolution)

if __name__ == "__main__":
    main()