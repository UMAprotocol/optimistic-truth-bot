import os
import requests
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
MLB_API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")

# Constants for the game and resolution mapping
GAME_DATE = "2025-04-18"
TEAM1_NAME = "Miami Marlins"
TEAM2_NAME = "Philadelphia Phillies"
RESOLUTION_MAP = {
    "MIA": "p2",  # Miami Marlins win
    "PHI": "p1",  # Philadelphia Phillies win
    "50-50": "p3",  # Game canceled or postponed without resolution
    "Too early to resolve": "p4"  # Data not available or game not completed
}

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_game_data():
    """
    Fetches game data for the specified date and teams from the SportsDataIO MLB API.
    """
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{GAME_DATE}?key={MLB_API_KEY}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        games = response.json()
        
        for game in games:
            if (game['HomeTeam'] == TEAM1_NAME or game['AwayTeam'] == TEAM1_NAME) and \
               (game['HomeTeam'] == TEAM2_NAME or game['AwayTeam'] == TEAM2_NAME):
                return game
        return None
    except requests.RequestException as e:
        logging.error(f"API request failed: {e}")
        return None

def determine_resolution(game):
    """
    Determines the resolution based on the game's status and outcome.
    """
    if not game:
        return "p4"  # No game data available

    if game['Status'] == "Final":
        if game['HomeTeamRuns'] > game['AwayTeamRuns']:
            winner = game['HomeTeam']
        else:
            winner = game['AwayTeam']
        
        if winner == TEAM1_NAME:
            return RESOLUTION_MAP["MIA"]
        else:
            return RESOLUTION_MAP["PHI"]
    elif game['Status'] == "Canceled":
        return RESOLUTION_MAP["50-50"]
    elif game['Status'] == "Postponed":
        return "p4"  # Market remains open until the game is completed
    else:
        return "p4"  # Game not completed or data insufficient

def main():
    """
    Main function to fetch MLB game data and determine the resolution.
    """
    game_data = fetch_game_data()
    resolution = determine_resolution(game_data)
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()