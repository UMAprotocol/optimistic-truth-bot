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
    "Tigers": "p2",  # Detroit Tigers win maps to p2
    "Brewers": "p1",  # Milwaukee Brewers win maps to p1
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

def fetch_game_data(date, team1_name, team2_name):
    """
    Fetches game data for the specified date and teams.

    Args:
        date: Game date in YYYY-MM-DD format
        team1_name: First team name (full name)
        team2_name: Second team name (full name)

    Returns:
        Game data dictionary or None if not found
    """
    logger.info(f"Fetching game data for game between {team1_name} and {team2_name} on {date}")

    # Use the exact format from the API documentation with key as query parameter
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{date}?key={API_KEY}"
    
    try:
        logger.debug("Sending API request")
        response = requests.get(url)
        response.raise_for_status()
        games = response.json()
        logger.info(f"Retrieved {len(games)} games for {date}")

        # Find the specific game - the API returns an array of game objects
        for game in games:
            if (game['HomeTeam'] == team1_name or game['AwayTeam'] == team1_name) and \
               (game['HomeTeam'] == team2_name or game['AwayTeam'] == team2_name):
                logger.info(f"Found matching game: {game['AwayTeam']} @ {game['HomeTeam']}")
                return game

        logger.warning(f"No matching game found between {team1_name} and {team2_name} on {date}.")
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
        return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

    status = game.get("Status")
    home_score = game.get("HomeTeamRuns")
    away_score = game.get("AwayTeamRuns")
    home_team = game.get("HomeTeam")
    away_team = game.get("AwayTeam")

    logger.info(
        f"Game status: {status}, Score: {away_team} {away_score} - {home_team} {home_score}"
    )

    if status in ["Scheduled", "Delayed", "InProgress", "Suspended"]:
        logger.info(f"Game is {status}, too early to resolve")
        return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]
    elif status == "Final":
        if home_score > away_score:
            winner_team = home_team
        else:
            winner_team = away_team

        if winner_team == "DET":
            return "recommendation: " + RESOLUTION_MAP["Tigers"]
        elif winner_team == "MIL":
            return "recommendation: " + RESOLUTION_MAP["Brewers"]
        else:
            return "recommendation: " + RESOLUTION_MAP["50-50"]
    elif status in ["Postponed", "Canceled"]:
        return "recommendation: " + RESOLUTION_MAP["50-50"]
    else:
        logger.warning(f"Unexpected game state: {status}, defaulting to 'Too early to resolve'")
        return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

def main():
    """
    Main function to query MLB game data and determine the resolution.
    """
    date = "2025-04-15"
    team1_name = "DET"  # Detroit Tigers abbreviation
    team2_name = "MIL"  # Milwaukee Brewers abbreviation

    # Fetch game data
    game = fetch_game_data(date, team1_name, team2_name)
    
    # Determine resolution
    resolution = determine_resolution(game)
    
    # Output the recommendation
    print(resolution)

if __name__ == "__main__":
    main()