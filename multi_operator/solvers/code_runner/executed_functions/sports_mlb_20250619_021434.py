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
DATE = "2025-06-18"
TEAM1 = "NYY"  # New York Yankees
TEAM2 = "LAA"  # Los Angeles Angels
RESOLUTION_MAP = {
    "Yankees": "p1",
    "Angels": "p2",
    "50-50": "p3",
    "Too early to resolve": "p4"
}

# API Endpoints
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/"
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

def get_games_by_date(date):
    url = f"{PRIMARY_ENDPOINT}{date}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        return None

def resolve_market(games, team1, team2):
    if not games:
        return RESOLUTION_MAP["Too early to resolve"]
    
    for game in games:
        if game['HomeTeam'] == team1 and game['AwayTeam'] == team2 or \
           game['HomeTeam'] == team2 and game['AwayTeam'] == team1:
            if game['Status'] == "Final":
                home_score = game['HomeTeamRuns']
                away_score = game['AwayTeamRuns']
                if home_score > away_score:
                    winner = game['HomeTeam']
                else:
                    winner = game['AwayTeam']
                
                if winner == team1:
                    return RESOLUTION_MAP["Yankees"]
                else:
                    return RESOLUTION_MAP["Angels"]
            elif game['Status'] == "Canceled":
                return RESOLUTION_MAP["50-50"]
            elif game['Status'] == "Postponed":
                return RESOLUTION_MAP["Too early to resolve"]
    
    return RESOLUTION_MAP["Too early to resolve"]

if __name__ == "__main__":
    games = get_games_by_date(DATE)
    result = resolve_market(games, TEAM1, TEAM2)
    print(f"recommendation: {result}")