import os
import requests
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
NHL_API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")

# Constants
RESOLUTION_MAP = {
    "NJD": "p2",  # New Jersey Devils
    "CAR": "p1",  # Carolina Hurricanes
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

def fetch_nhl_game_data():
    """
    Fetches NHL game data for the specified game.
    """
    url = f"https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/2025-04-20?key={NHL_API_KEY}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        games = response.json()
        for game in games:
            if game['HomeTeam'] == 'CAR' and game['AwayTeam'] == 'NJD' or game['HomeTeam'] == 'NJD' and game['AwayTeam'] == 'CAR':
                return game
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch NHL game data: {e}")
        return None

def determine_resolution(game):
    """
    Determines the resolution based on the game's status and outcome.
    """
    if not game:
        return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

    if game['Status'] == 'Final':
        if game['HomeTeam'] == 'NJD' and game['HomeTeamScore'] > game['AwayTeamScore']:
            return "recommendation: " + RESOLUTION_MAP["NJD"]
        elif game['AwayTeam'] == 'NJD' and game['AwayTeamScore'] > game['HomeTeamScore']:
            return "recommendation: " + RESOLUTION_MAP["NJD"]
        elif game['HomeTeam'] == 'CAR' and game['HomeTeamScore'] > game['AwayTeamScore']:
            return "recommendation: " + RESOLUTION_MAP["CAR"]
        elif game['AwayTeam'] == 'CAR' and game['AwayTeamScore'] > game['HomeTeamScore']:
            return "recommendation: " + RESOLUTION_MAP["CAR"]
    elif game['Status'] == 'Canceled':
        return "recommendation: " + RESOLUTION_MAP["50-50"]
    elif game['Status'] == 'Postponed':
        return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

    return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

def main():
    """
    Main function to fetch NHL game data and determine the resolution.
    """
    game_data = fetch_nhl_game_data()
    resolution = determine_resolution(game_data)
    print(resolution)

if __name__ == "__main__":
    main()