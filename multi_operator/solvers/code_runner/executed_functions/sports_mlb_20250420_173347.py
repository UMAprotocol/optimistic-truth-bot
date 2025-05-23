import os
import requests
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")

# Constants for resolution mapping
RESOLUTION_MAP = {
    "Mumbai Indians": "p2",
    "Chennai Super Kings": "p1",
    "50-50": "p3",
    "Too early to resolve": "p4",
}

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

def fetch_game_data():
    """
    Fetches game data for the IPL game between Mumbai Indians and Chennai Super Kings.
    """
    date = "2025-04-20"
    team1 = "Mumbai Indians"
    team2 = "Chennai Super Kings"
    url = f"https://api.sportsdata.io/v3/cricket/scores/json/GamesByDate/{date}?key={API_KEY}"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        games = response.json()

        for game in games:
            if game['HomeTeamName'] == team1 and game['AwayTeamName'] == team2:
                return game
            elif game['HomeTeamName'] == team2 and game['AwayTeamName'] == team1:
                return game
        logger.info("No matching game found.")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching game data: {e}")
        return None

def determine_resolution(game):
    """
    Determines the resolution based on the game's status and outcome.
    """
    if not game:
        return "p4"  # Too early to resolve

    if game['Status'] == "Canceled":
        return RESOLUTION_MAP["50-50"]
    elif game['Status'] == "Postponed":
        return "p4"  # Market remains open
    elif game['Status'] == "Final":
        if game['HomeTeamRuns'] > game['AwayTeamRuns']:
            return RESOLUTION_MAP[game['HomeTeamName']]
        elif game['AwayTeamRuns'] > game['HomeTeamRuns']:
            return RESOLUTION_MAP[game['AwayTeamName']]
        else:
            return RESOLUTION_MAP["50-50"]
    else:
        return "p4"  # Game not completed yet

def main():
    """
    Main function to determine the resolution of the IPL game market.
    """
    game_data = fetch_game_data()
    resolution = determine_resolution(game_data)
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()