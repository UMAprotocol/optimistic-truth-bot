import os
import requests
import logging
from datetime import datetime, timedelta
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
DATE = "2025-06-10"
TEAM1 = "Cincinnati Reds"
TEAM2 = "Cleveland Guardians"
RESOLUTION_MAP = {
    "Cincinnati Reds": "p2",
    "Cleveland Guardians": "p1",
    "50-50": "p3",
    "Too early to resolve": "p4"
}

# API Configuration
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
BASE_URL = "https://api.sportsdata.io/v3/mlb/scores/json"

def get_data(url, params=None):
    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Request failed: {e}")
        return None

def find_game(date, team1, team2):
    formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m-%d")
    games = get_data(f"{BASE_URL}/GamesByDate/{formatted_date}")
    if games:
        for game in games:
            if (game['HomeTeam'] == team1 and game['AwayTeam'] == team2) or \
               (game['HomeTeam'] == team2 and game['AwayTeam'] == team1):
                return game
    return None

def resolve_market(game):
    if not game:
        return RESOLUTION_MAP["Too early to resolve"]
    if game['Status'] == "Final":
        home_team = game['HomeTeam']
        away_team = game['AwayTeam']
        home_score = game['HomeTeamRuns']
        away_score = game['AwayTeamRuns']
        if home_score > away_score:
            return RESOLUTION_MAP[home_team]
        elif away_score > home_score:
            return RESOLUTION_MAP[away_team]
    elif game['Status'] == "Canceled":
        return RESOLUTION_MAP["50-50"]
    elif game['Status'] == "Postponed":
        return RESOLUTION_MAP["Too early to resolve"]
    return RESOLUTION_MAP["Too early to resolve"]

if __name__ == "__main__":
    game = find_game(DATE, TEAM1, TEAM2)
    result = resolve_market(game)
    print(f"recommendation: {result}")