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
    "CHW": "p2",  # Chicago White Sox win
    "MIN": "p1",  # Minnesota Twins win
    "50-50": "p3",  # Game canceled or unresolved
    "Too early to resolve": "p4",  # Data not available or game not completed
}

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_game_data():
    """
    Fetches game data for the specified MLB game.
    """
    date = "2025-04-22"
    team1 = "CHW"
    team2 = "MIN"
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{date}?key={MLB_API_KEY}"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        games = response.json()

        for game in games:
            if game['HomeTeam'] == team1 and game['AwayTeam'] == team2 or game['HomeTeam'] == team2 and game['AwayTeam'] == team1:
                return game
        return None
    except requests.exceptions.RequestException as e:
        logging.error(f"API request failed: {e}")
        return None

def resolve_market(game):
    """
    Resolves the market based on the game data.
    """
    if not game:
        return "recommendation: p4"  # No game data available

    if game['Status'] == "Final":
        home_team = game['HomeTeam']
        away_team = game['AwayTeam']
        home_score = game['HomeTeamRuns']
        away_score = game['AwayTeamRuns']

        if home_score > away_score:
            winner = home_team
        else:
            winner = away_team

        return f"recommendation: {RESOLUTION_MAP.get(winner, 'p3')}"
    elif game['Status'] == "Canceled":
        return "recommendation: p3"
    elif game['Status'] == "Postponed":
        return "recommendation: p4"
    else:
        return "recommendation: p4"

def main():
    """
    Main function to execute the market resolution logic.
    """
    game_data = fetch_game_data()
    result = resolve_market(game_data)
    print(result)

if __name__ == "__main__":
    main()