import os
import requests
from dotenv import load_dotenv
from datetime import datetime
import logging

# Load API key from .env file
load_dotenv()
MLB_API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")

# Constants for team names and date
GAME_DATE = "2025-04-18"
TEAM1_NAME = "San Francisco Giants"
TEAM2_NAME = "Los Angeles Angels"

# Resolution mapping
RESOLUTION_MAP = {
    "SFG": "p2",  # San Francisco Giants win
    "LAA": "p1",  # Los Angeles Angels win
    "50-50": "p3",  # Game canceled or postponed without resolution
    "Too early to resolve": "p4",  # Data not available or game not completed
}

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_game_data(date):
    """
    Fetches game data for the specified date.
    """
    primary_url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{date}?key={MLB_API_KEY}"
    proxy_url = f"https://minimal-ubuntu-production.up.railway.app/sportsdata-proxy/mlb/GamesByDate/{date}?key={MLB_API_KEY}"

    try:
        # Try proxy endpoint first
        response = requests.get(proxy_url, timeout=10)
        if response.status_code != 200:
            # Fallback to primary endpoint if proxy fails
            response = requests.get(primary_url, timeout=10)
        response.raise_for_status()
        games = response.json()

        # Find the game between the specified teams
        for game in games:
            if (game['HomeTeam'] == "SFG" and game['AwayTeam'] == "LAA") or (game['HomeTeam'] == "LAA" and game['AwayTeam'] == "SFG"):
                return game
        return None
    except requests.RequestException as e:
        logging.error(f"Failed to fetch game data: {e}")
        return None

def determine_resolution(game):
    """
    Determines the resolution based on the game's status and outcome.
    """
    if not game:
        return "recommendation: p4"

    status = game['Status']
    if status == "Final":
        home_team = game['HomeTeam']
        away_team = game['AwayTeam']
        home_score = game['HomeTeamRuns']
        away_score = game['AwayTeamRuns']

        if home_score > away_score:
            return f"recommendation: {RESOLUTION_MAP[home_team]}"
        else:
            return f"recommendation: {RESOLUTION_MAP[away_team]}"
    elif status in ["Canceled", "Postponed"]:
        return "recommendation: p3"
    else:
        return "recommendation: p4"

def main():
    """
    Main function to query MLB game data and determine the resolution.
    """
    game_data = fetch_game_data(GAME_DATE)
    resolution = determine_resolution(game_data)
    print(resolution)

if __name__ == "__main__":
    main()