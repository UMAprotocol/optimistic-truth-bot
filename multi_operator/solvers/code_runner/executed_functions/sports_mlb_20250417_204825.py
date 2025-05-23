import os
import requests
from dotenv import load_dotenv
from datetime import datetime
import logging

# Load API key from .env file
load_dotenv()
MLB_API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")

# Constants for resolution mapping
RESOLUTION_MAP = {
    "Athletics": "p2",  # Athletics win maps to p2
    "Chicago White Sox": "p1",  # Chicago White Sox win maps to p1
    "50-50": "p3",  # Canceled or no make-up game maps to p3
    "Too early to resolve": "p4",  # Incomplete data maps to p4
}

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

def fetch_game_data(api_key, date):
    """
    Fetches game data for the specified date.
    """
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{date}?key={api_key}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        games = response.json()
        return games
    except requests.RequestException as e:
        logger.error(f"Failed to fetch game data: {e}")
        return None

def determine_resolution(games):
    """
    Determines the resolution based on the game's status and outcome.
    """
    for game in games:
        if game['HomeTeam'] == "CWS" and game['AwayTeam'] == "OAK":
            if game['Status'] == "Final":
                home_score = game['HomeTeamRuns']
                away_score = game['AwayTeamRuns']
                if home_score > away_score:
                    return "recommendation: p1"  # Chicago White Sox win
                elif away_score > home_score:
                    return "recommendation: p2"  # Athletics win
            elif game['Status'] == "Canceled":
                return "recommendation: p3"  # Canceled game
            elif game['Status'] in ["Scheduled", "InProgress", "Delayed", "Suspended"]:
                return "recommendation: p4"  # Game not completed
    return "recommendation: p4"  # No matching game found or other cases

def main():
    """
    Main function to determine the resolution of the MLB game.
    """
    date = "2025-04-17"
    if not MLB_API_KEY:
        logger.error("API key for MLB data is not set.")
        print("recommendation: p4")
        return

    games = fetch_game_data(MLB_API_KEY, date)
    if games is None:
        print("recommendation: p4")
    else:
        resolution = determine_resolution(games)
        print(resolution)

if __name__ == "__main__":
    main()