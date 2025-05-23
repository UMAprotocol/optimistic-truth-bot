import os
import requests
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")

# Constants
RESOLUTION_MAP = {
    "MIL": "p2",  # Milwaukee Bucks
    "IND": "p1",  # Indiana Pacers
    "50-50": "p3",
    "Too early to resolve": "p4",
}

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_nba_game_data(game_date, home_team, away_team):
    """
    Fetches NBA game data for a specific date and teams.
    """
    url = f"https://api.sportsdata.io/v3/nba/scores/json/GamesByDate/{game_date}?key={API_KEY}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        games = response.json()
        for game in games:
            if game['HomeTeam'] == home_team and game['AwayTeam'] == away_team:
                return game
        return None
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching NBA game data: {e}")
        return None

def resolve_market(game_data):
    """
    Resolves the market based on the game data.
    """
    if not game_data:
        return "p4"  # No data available, cannot resolve

    if game_data['Status'] == "Canceled":
        return RESOLUTION_MAP["50-50"]
    elif game_data['Status'] == "Postponed":
        return "p4"  # Market remains open
    elif game_data['Status'] == "Final":
        home_score = game_data['HomeTeamScore']
        away_score = game_data['AwayTeamScore']
        if home_score > away_score:
            return RESOLUTION_MAP[game_data['HomeTeam']]
        elif away_score > home_score:
            return RESOLUTION_MAP[game_data['AwayTeam']]
    return "p4"  # In case of any other status, we cannot resolve yet

def main():
    game_date = "2025-04-22"
    home_team = "IND"  # Indiana Pacers
    away_team = "MIL"  # Milwaukee Bucks

    game_data = fetch_nba_game_data(game_date, home_team, away_team)
    resolution = resolve_market(game_data)
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()