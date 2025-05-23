import os
import requests
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
MLB_API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")

# Check if API key is available
if not MLB_API_KEY:
    raise ValueError("SPORTS_DATA_IO_MLB_API_KEY not found in environment variables.")

# Constants for resolution mapping
RESOLUTION_MAP = {
    "TEX": "p2",  # Texas Rangers win
    "OAK": "p1",  # Athletics win
    "50-50": "p3",  # Game canceled or postponed without resolution
    "Too early to resolve": "p4",  # Data not available or game not completed
}

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_game_data():
    """
    Fetches game data for the Texas Rangers vs. Athletics game on the specified date.
    """
    date = "2025-04-22"
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{date}?key={MLB_API_KEY}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        games = response.json()
        for game in games:
            if game['HomeTeam'] in ['TEX', 'OAK'] and game['AwayTeam'] in ['TEX', 'OAK']:
                return game
        return None
    except requests.RequestException as e:
        logging.error(f"Error fetching game data: {e}")
        return None

def determine_resolution(game):
    """
    Determines the resolution based on the game's status and outcome.
    """
    if not game:
        return "p4"  # No data available

    if game['Status'] == "Final":
        if game['HomeTeamRuns'] > game['AwayTeamRuns']:
            winner = game['HomeTeam']
        else:
            winner = game['AwayTeam']
        return RESOLUTION_MAP.get(winner, "p4")
    elif game['Status'] in ["Canceled", "Postponed"]:
        return "p3"
    else:
        return "p4"

def main():
    """
    Main function to determine the resolution of the Texas Rangers vs. Athletics game.
    """
    game_data = fetch_game_data()
    resolution = determine_resolution(game_data)
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()