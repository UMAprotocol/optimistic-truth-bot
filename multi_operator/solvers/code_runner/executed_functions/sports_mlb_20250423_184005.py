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
    "Too early to resolve": "p4",  # Game not yet played or data unavailable
}

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_game_data():
    """
    Fetches game data for the specified MLB game between St. Louis Cardinals and Atlanta Braves.
    """
    date = "2025-04-23"
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{date}?key={MLB_API_KEY}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        games = response.json()
        for game in games:
            if game['HomeTeam'] == 'STL' and game['AwayTeam'] == 'ATL':
                return game
            elif game['HomeTeam'] == 'ATL' and game['AwayTeam'] == 'STL':
                return game
    except requests.exceptions.RequestException as e:
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
            return RESOLUTION_MAP[game['HomeTeam']]
        elif game['AwayTeamRuns'] > game['HomeTeamRuns']:
            return RESOLUTION_MAP[game['AwayTeam']]
    elif game['Status'] == "Canceled":
        return "p3"  # Game canceled
    elif game['Status'] == "Postponed":
        return "p4"  # Game postponed, resolution pending

    return "p4"  # Default case if none of the above conditions are met

def main():
    """
    Main function to determine the outcome of the MLB game between St. Louis Cardinals and Atlanta Braves.
    """
    game_data = fetch_game_data()
    resolution = determine_resolution(game_data)
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()