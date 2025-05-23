import os
import requests
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")

# Constants for resolution mapping
RESOLUTION_MAP = {
    "GT": "p2",  # Gujarat Titans
    "DC": "p1",  # Delhi Capitals
    "50-50": "p3",
    "Too early to resolve": "p4",
}

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

def fetch_ipl_game_data():
    """
    Fetches game data for the specified IPL game.
    """
    # Define the URL and parameters for the API request
    url = "https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/2025-04-19"
    headers = {
        "Ocp-Apim-Subscription-Key": API_KEY
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        games = response.json()

        # Search for the specific game
        for game in games:
            if game['HomeTeam'] == "GT" and game['AwayTeam'] == "DC":
                return game
            elif game['HomeTeam'] == "DC" and game['AwayTeam'] == "GT":
                return game

        logger.info("No game found for the specified teams on the given date.")
        return None

    except requests.RequestException as e:
        logger.error(f"Error fetching game data: {e}")
        return None

def determine_resolution(game):
    """
    Determines the resolution based on the game's status and outcome.
    """
    if not game:
        return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

    if game['Status'] == "Final":
        if game['HomeTeam'] == "GT" and game['HomeTeamScore'] > game['AwayTeamScore']:
            return "recommendation: " + RESOLUTION_MAP["GT"]
        elif game['AwayTeam'] == "GT" and game['AwayTeamScore'] > game['HomeTeamScore']:
            return "recommendation: " + RESOLUTION_MAP["GT"]
        elif game['HomeTeam'] == "DC" and game['HomeTeamScore'] > game['AwayTeamScore']:
            return "recommendation: " + RESOLUTION_MAP["DC"]
        elif game['AwayTeam'] == "DC" and game['AwayTeamScore'] > game['HomeTeamScore']:
            return "recommendation: " + RESOLUTION_MAP["DC"]
    elif game['Status'] == "Canceled":
        return "recommendation: " + RESOLUTION_MAP["50-50"]
    elif game['Status'] == "Postponed":
        return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

    return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

def main():
    """
    Main function to fetch IPL game data and determine the resolution.
    """
    game_data = fetch_ipl_game_data()
    resolution = determine_resolution(game_data)
    print(resolution)

if __name__ == "__main__":
    main()