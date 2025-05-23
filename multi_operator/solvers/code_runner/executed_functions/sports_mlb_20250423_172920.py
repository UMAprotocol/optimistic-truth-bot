import os
import requests
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")

# Constants for resolution mapping
RESOLUTION_MAP = {
    "Sunrisers Hyderabad": "p2",  # Sunrisers Hyderabad win maps to p2
    "Mumbai Indians": "p1",       # Mumbai Indians win maps to p1
    "50-50": "p3",                # Canceled or no make-up game maps to p3
    "Too early to resolve": "p4"  # Incomplete data maps to p4
}

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

def fetch_game_data():
    """
    Fetches game data for the IPL match between Sunrisers Hyderabad and Mumbai Indians.
    """
    date = "2025-04-23"
    team1 = "Sunrisers Hyderabad"
    team2 = "Mumbai Indians"
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
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        return None

def determine_resolution(game):
    """
    Determines the resolution based on the game's status and outcome.
    """
    if not game:
        return RESOLUTION_MAP["Too early to resolve"]

    if game['Status'] == "Canceled":
        return RESOLUTION_MAP["50-50"]
    elif game['Status'] == "Final":
        if game['HomeTeamRuns'] > game['AwayTeamRuns']:
            return RESOLUTION_MAP[game['HomeTeamName']]
        elif game['AwayTeamRuns'] > game['HomeTeamRuns']:
            return RESOLUTION_MAP[game['AwayTeamName']]
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