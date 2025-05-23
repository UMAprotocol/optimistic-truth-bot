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
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

def fetch_game_data():
    """
    Fetches game data for the specified IPL match between Kolkata Knight Riders and Gujarat Titans.
    """
    # Define the date and teams for the IPL match
    date = "2025-04-21"
    team1 = "Kolkata Knight Riders"
    team2 = "Gujarat Titans"

    # API endpoint configuration
    url = f"https://api.sportsdata.io/v3/cricket/scores/json/GamesByDate/{date}?key={API_KEY}"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        games = response.json()

        # Find the game between the specified teams
        for game in games:
            if team1 in game['HomeTeamName'] and team2 in game['AwayTeamName']:
                return game
            elif team2 in game['HomeTeamName'] and team1 in game['AwayTeamName']:
                return game
        logger.info("No game found for the specified teams on the given date.")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch game data: {e}")
        return None

def determine_resolution(game):
    """
    Determines the resolution based on the game's status and outcome.
    """
    if not game:
        return "p4"  # Too early to resolve

    status = game.get('Status')
    if status == "Final":
        if game['HomeTeamRuns'] > game['AwayTeamRuns']:
            winner = game['HomeTeamName']
        else:
            winner = game['AwayTeamName']

        if winner == "Kolkata Knight Riders":
            return "p2"  # Kolkata Knight Riders win
        elif winner == "Gujarat Titans":
            return "p1"  # Gujarat Titans win
    elif status in ["Canceled", "Postponed"]:
        return "p3"  # Game not played or postponed, resolve as 50-50

    return "p4"  # If none of the above, it's too early to resolve

def main():
    """
    Main function to fetch IPL game data and determine the resolution.
    """
    game_data = fetch_game_data()
    resolution = determine_resolution(game_data)
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()