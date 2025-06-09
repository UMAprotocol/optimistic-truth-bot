import os
import requests
import logging
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# Constants
DATE = "2025-06-06"
TEAM1 = "SD"  # San Diego Padres
TEAM2 = "MIL"  # Milwaukee Brewers
GAME_DATE = datetime.strptime(DATE, "%Y-%m-%d").date()

# API Endpoints
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/"
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

def get_game_data(date):
    url = f"{PRIMARY_ENDPOINT}{date}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        games = response.json()
        for game in games:
            if game['HomeTeam'] == TEAM2 and game['AwayTeam'] == TEAM1:
                return game
        return None
    except requests.RequestException as e:
        logger.error(f"Error fetching game data: {e}")
        return None

def resolve_market(game):
    if not game:
        return "p4"  # Game not found, cannot resolve yet
    if game['Status'] == "Final":
        home_score = game['HomeTeamRuns']
        away_score = game['AwayTeamRuns']
        if home_score > away_score:
            return "p1"  # Brewers win
        elif away_score > home_score:
            return "p2"  # Padres win
    elif game['Status'] == "Postponed":
        return "p4"  # Game postponed, check later
    elif game['Status'] == "Canceled":
        return "p3"  # Game canceled, resolve 50-50
    return "p4"  # In case of any other status, consider it unresolved

if __name__ == "__main__":
    game_info = get_game_data(GAME_DATE)
    result = resolve_market(game_info)
    print(f"recommendation: {result}")