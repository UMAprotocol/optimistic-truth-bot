import os
import requests
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")

# Constants for resolution mapping
RESOLUTION_MAP = {
    "Kolkata Knight Riders": "p2",
    "Gujarat Titans": "p1",
    "50-50": "p3",
    "Too early to resolve": "p4",
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
    # Define the URL for the IPL game data
    url = f"https://api.sportsdata.io/v3/cricket/scores/json/GamesByDate/2025-04-21?key={API_KEY}"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        games = response.json()
        
        # Search for the specific game
        for game in games:
            if game['HomeTeamName'] == "Kolkata Knight Riders" and game['AwayTeamName'] == "Gujarat Titans":
                return game
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch game data: {e}")
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

    if game['Status'] == "Final":
        if game['Winner'] == "Kolkata Knight Riders":
            return RESOLUTION_MAP["Kolkata Knight Riders"]
        elif game['Winner'] == "Gujarat Titans":
            return RESOLUTION_MAP["Gujarat Titans"]
    elif game['Status'] == "Canceled":
        return RESOLUTION_MAP["50-50"]
    elif game['Status'] == "Postponed":
        return RESOLUTION_MAP["Too early to resolve"]

    return RESOLUTION_MAP["Too early to resolve"]

def main():
    """
    Main function to determine the resolution of the IPL game.
    """
    game_data = fetch_game_data()
    resolution = determine_resolution(game_data)
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()