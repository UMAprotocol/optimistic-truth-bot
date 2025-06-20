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
DATE = "2025-06-12"
TEAM1 = "Detroit Tigers"
TEAM2 = "Baltimore Orioles"
RESOLUTION_MAP = {
    "Tigers": "p2",
    "Orioles": "p1",
    "50-50": "p3",
    "Too early to resolve": "p4"
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
                return RESOLUTION_MAP.get(winner, "Too early to resolve")
            elif game['Status'] == "Canceled":
                return RESOLUTION_MAP["50-50"]
            elif game['Status'] == "Postponed":
                return RESOLUTION_MAP["Too early to resolve"]
    return RESOLUTION_MAP["Too early to resolve"]

def main():
    games = get_games_by_date(DATE)
    if games:
        result = resolve_market(games, TEAM1, TEAM2)
        print(f"recommendation: {result}")
    else:
        print("recommendation: p4")

if __name__ == "__main__":
    main()