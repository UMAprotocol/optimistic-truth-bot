import os
import requests
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")

# Check if API key is available
if not API_KEY:
    raise ValueError("SPORTS_DATA_IO_MLB_API_KEY not found in environment variables. Please add it to your .env file.")

# Constants - RESOLUTION MAPPING using internal abbreviations
RESOLUTION_MAP = {
    "Sunrisers Hyderabad": "p2",  # Sunrisers Hyderabad win maps to p2
    "Mumbai Indians": "p1",  # Mumbai Indians win maps to p1
    "50-50": "p3",  # Canceled or postponed game maps to p3
    "Too early to resolve": "p4",  # Incomplete data maps to p4
}

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

def fetch_game_data():
    """
    Fetches game data for the specified IPL game.

    Returns:
        Game data dictionary or None if not found
    """
    date = "2025-04-23"
    team1_name = "Sunrisers Hyderabad"
    team2_name = "Mumbai Indians"
    url = f"https://api.sportsdata.io/v3/cricket/scores/json/GamesByDate/{date}?key={API_KEY}"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        games = response.json()

        for game in games:
            if game['HomeTeamName'] == team1_name and game['AwayTeamName'] == team2_name:
                return game
            elif game['HomeTeamName'] == team2_name and game['AwayTeamName'] == team1_name:
                return game

        logger.info("No matching game found.")
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
        home_score = game.get("HomeTeamScore")
        away_score = game.get("AwayTeamScore")
        if home_score > away_score:
            return RESOLUTION_MAP[game.get("HomeTeamName")]
        else:
            return RESOLUTION_MAP[game.get("AwayTeamName")]
    elif status in ["Canceled", "Postponed"]:
        return RESOLUTION_MAP["50-50"]
    else:
        return RESOLUTION_MAP["Too early to resolve"]

def main():
    """
    Main function to query IPL game data and determine the resolution.
    """
    game = fetch_game_data()
    resolution = determine_resolution(game)
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()