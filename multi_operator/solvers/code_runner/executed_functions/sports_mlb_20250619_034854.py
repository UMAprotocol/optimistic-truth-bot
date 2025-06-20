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
TEAM1 = "Minnesota Twins"
TEAM2 = "Cincinnati Reds"
RESOLUTION_MAP = {
    TEAM1: "p2",  # Twins win
    TEAM2: "p1",  # Reds win
    "50-50": "p3",  # Game canceled or tie
    "Too early to resolve": "p4"  # Not enough data or game not completed
}

# API Configuration
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
BASE_URL = "https://api.sportsdata.io/v3/mlb/scores/json"

def get_games_by_date(date):
    url = f"{BASE_URL}/GamesByDate/{date}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    else:
        logger.error(f"Failed to fetch games for date {date}: {response.status_code}")
        return None

def resolve_market(games, team1, team2):
    if not games:
        return RESOLUTION_MAP["Too early to resolve"]
    
    for game in games:
        if (game['HomeTeam'] == team1 or game['AwayTeam'] == team1) and \
           (game['HomeTeam'] == team2 or game['AwayTeam'] == team2):
            if game['Status'] == "Final":
                home_team_runs = game['HomeTeamRuns']
                away_team_runs = game['AwayTeamRuns']
                if home_team_runs > away_team_runs:
                    winner = game['HomeTeam']
                else:
                    winner = game['AwayTeam']
                return RESOLUTION_MAP[winner]
            elif game['Status'] in ["Canceled", "Postponed"]:
                return RESOLUTION_MAP["50-50"]
            else:
                return RESOLUTION_MAP["Too early to resolve"]
    return RESOLUTION_MAP["Too early to resolve"]

if __name__ == "__main__":
    games = get_games_by_date(DATE)
    recommendation = resolve_market(games, TEAM1, TEAM2)
    print(f"recommendation: {recommendation}")