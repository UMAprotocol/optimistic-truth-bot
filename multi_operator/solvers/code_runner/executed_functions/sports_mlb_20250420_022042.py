import os
import requests
from dotenv import load_dotenv
from datetime import datetime
import logging

# Load API key from .env file
load_dotenv()
MLB_API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")

# Constants - RESOLUTION MAPPING using team names
RESOLUTION_MAP = {
    "Twins": "p2",  # Minnesota Twins win maps to p2
    "Braves": "p1",  # Atlanta Braves win maps to p1
    "50-50": "p3",  # Canceled or no make-up game maps to p3
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
    Fetches game data for the specified date and teams.
    """
    date = "2025-04-19"
    team1_name = "Minnesota Twins"
    team2_name = "Atlanta Braves"
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{date}?key={MLB_API_KEY}"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        games = response.json()

        for game in games:
            if (game['HomeTeam'] == "MIN" and game['AwayTeam'] == "ATL") or (game['HomeTeam'] == "ATL" and game['AwayTeam'] == "MIN"):
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
        return "p4"  # No game data available

    if game['Status'] == "Final":
        if game['HomeTeamRuns'] > game['AwayTeamRuns']:
            winner = "Twins" if game['HomeTeam'] == "MIN" else "Braves"
        else:
            winner = "Braves" if game['HomeTeam'] == "ATL" else "Twins"
        return RESOLUTION_MAP[winner]
    elif game['Status'] == "Canceled":
        return "p3"
    elif game['Status'] == "Postponed":
        # Check if the game is rescheduled within the season
        if 'RescheduledGameID' in game and game['RescheduledGameID'] is not None:
            return "p4"  # Game is postponed but rescheduled
        else:
            return "p3"  # Game is postponed and not rescheduled
    else:
        return "p4"  # Game is not yet completed or other statuses

def main():
    """
    Main function to determine the resolution of the MLB game.
    """
    game_data = fetch_game_data()
    resolution = determine_resolution(game_data)
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()