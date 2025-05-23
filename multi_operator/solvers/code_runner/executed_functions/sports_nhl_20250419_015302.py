import os
import requests
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")

# Constants for resolution mapping
RESOLUTION_MAP = {
    "MIA": "p2",  # Miami Heat win maps to p2
    "ATL": "p1",  # Atlanta Hawks win maps to p1
    "50-50": "p3",  # Game canceled or unresolved maps to p3
    "Too early to resolve": "p4",  # Incomplete data maps to p4
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
    Fetches game data for the Miami Heat vs Atlanta Hawks game scheduled on 2025-04-18.
    """
    url = f"https://api.sportsdata.io/v3/nba/scores/json/GamesByDate/2025-04-18?key={API_KEY}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        games = response.json()
        for game in games:
            if game['HomeTeam'] == 'MIA' and game['AwayTeam'] == 'ATL' or game['HomeTeam'] == 'ATL' and game['AwayTeam'] == 'MIA':
                return game
        logger.info("No game found between Miami Heat and Atlanta Hawks on the specified date.")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch game data: {e}")
        return None

def determine_resolution(game):
    """
    Determines the resolution based on the game's status and outcome.
    """
    if not game:
        return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

    status = game.get("Status")
    if status == "Final":
        home_team = game['HomeTeam']
        away_team = game['AwayTeam']
        home_score = game['HomeTeamScore']
        away_score = game['AwayTeamScore']
        if home_score > away_score:
            winner = home_team
        else:
            winner = away_team
        return "recommendation: " + RESOLUTION_MAP[winner]
    elif status == "Canceled":
        return "recommendation: " + RESOLUTION_MAP["50-50"]
    elif status == "Postponed":
        return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]
    else:
        return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

def main():
    game_data = fetch_game_data()
    resolution = determine_resolution(game_data)
    print(resolution)

if __name__ == "__main__":
    main()