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
    "SFG": "p2",  # San Francisco Giants win maps to p2
    "LAA": "p1",  # Los Angeles Angels win maps to p1
    "50-50": "p3",  # Tie or undetermined maps to p3
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
        if game['HomeTeam'] == 'LAA' and game['AwayTeam'] == 'SFG' or game['HomeTeam'] == 'SFG' and game['AwayTeam'] == 'LAA':
            if game['Status'] == 'Final':
                home_score = game['HomeTeamRuns']
                away_score = game['AwayTeamRuns']
                if home_score > away_score:
                    winner = game['HomeTeam']
                else:
                    winner = game['AwayTeam']
                return RESOLUTION_MAP.get(winner, "p4")
            elif game['Status'] in ['Canceled', 'Postponed']:
                return "p3"
            else:
                return "p4"
    return "p4"

def main():
    """
    Main function to query MLB game data and determine the resolution.
    """
    date = "2025-04-19"
    if not MLB_API_KEY:
        logger.error("API key is not set. Please check your .env file.")
        print("recommendation: p4")
        return

    games = fetch_game_data(MLB_API_KEY, date)
    if games is None:
        print("recommendation: p4")
        return

    resolution = determine_resolution(games)
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()