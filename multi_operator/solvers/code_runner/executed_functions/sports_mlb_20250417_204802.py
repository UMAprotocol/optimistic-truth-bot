import os
import requests
from dotenv import load_dotenv
from datetime import datetime
import logging

# Load environment variables
load_dotenv()
MLB_API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")

# Constants for resolution mapping
RESOLUTION_MAP = {
    "Athletics": "p2",  # Athletics win maps to p2
    "Chicago White Sox": "p1",  # Chicago White Sox win maps to p1
    "50-50": "p3",  # Game canceled or unresolved maps to p3
    "Too early to resolve": "p4",  # Game not yet played or no data available maps to p4
}

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_game_data():
    """
    Fetches game data for the specified MLB game.
    """
    date = "2025-04-17"
    team1 = "Athletics"
    team2 = "Chicago White Sox"
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{date}?key={MLB_API_KEY}"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        games = response.json()

        for game in games:
            if (game['HomeTeam'] == team1 and game['AwayTeam'] == team2) or (game['HomeTeam'] == team2 and game['AwayTeam'] == team1):
                return game
        return None
    except requests.RequestException as e:
        logging.error(f"Error fetching game data: {e}")
        return None

def resolve_market(game):
    """
    Resolves the market based on the game data.
    """
    if game is None:
        return "p4"  # No game data found

    if game['Status'] == "Final":
        if game['HomeTeamRuns'] > game['AwayTeamRuns']:
            winner = game['HomeTeam']
        else:
            winner = game['AwayTeam']

        return RESOLUTION_MAP.get(winner, "p3")
    elif game['Status'] in ["Canceled", "Postponed"]:
        return "p3"
    else:
        return "p4"

def main():
    game_data = fetch_game_data()
    resolution = resolve_market(game_data)
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()