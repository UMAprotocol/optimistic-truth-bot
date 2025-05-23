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
    "STL": "p2",  # St. Louis Cardinals win
    "ATL": "p1",  # Atlanta Braves win
    "50-50": "p3",  # Game canceled or unresolved
    "Too early to resolve": "p4",  # Data not available or game not completed
}

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_game_data():
    """
    Fetches game data for the specified MLB game between St. Louis Cardinals and Atlanta Braves.
    """
    date = "2025-04-21"
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{date}?key={MLB_API_KEY}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        games = response.json()
        for game in games:
            if game['HomeTeam'] == 'STL' and game['AwayTeam'] == 'ATL' or game['HomeTeam'] == 'ATL' and game['AwayTeam'] == 'STL':
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
        return "recommendation: p4"  # No game data found

    if game['Status'] == 'Final':
        if game['HomeTeamRuns'] > game['AwayTeamRuns']:
            winner = game['HomeTeam']
        else:
            winner = game['AwayTeam']
        return f"recommendation: {RESOLUTION_MAP.get(winner, 'p3')}"
    elif game['Status'] in ['Canceled', 'Postponed']:
        return "recommendation: p3"
    else:
        return "recommendation: p4"  # Game not completed or data insufficient

def main():
    """
    Main function to process the MLB game data and determine the market resolution.
    """
    game_data = fetch_game_data()
    resolution = determine_resolution(game_data)
    print(resolution)

if __name__ == "__main__":
    main()