import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# Constants
DATE = "2025-06-14"
TEAM1 = "New York Yankees"
TEAM2 = "Boston Red Sox"
RESOLUTION_MAP = {
    TEAM1: "p2",  # Yankees win
    TEAM2: "p1",  # Red Sox win
    "Postponed": "p4",  # Game postponed
    "Canceled": "p3",  # Game canceled
    "Unknown": "p4"  # Unknown or in-progress
}

# Headers for API request
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

def get_game_info(date):
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{date}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        games = response.json()
        for game in games:
            if (game['HomeTeam'] == TEAM1 or game['AwayTeam'] == TEAM1) and \
               (game['HomeTeam'] == TEAM2 or game['AwayTeam'] == TEAM2):
                return game
    return None

def resolve_market(game):
    if not game:
        return "recommendation: " + RESOLUTION_MAP["Unknown"]
    if game['Status'] == "Final":
        if game['HomeTeamRuns'] > game['AwayTeamRuns']:
            winner = game['HomeTeam']
        else:
            winner = game['AwayTeam']
        return "recommendation: " + RESOLUTION_MAP[winner]
    elif game['Status'] == "Postponed":
        return "recommendation: " + RESOLUTION_MAP["Postponed"]
    elif game['Status'] == "Canceled":
        return "recommendation: " + RESOLUTION_MAP["Canceled"]
    else:
        return "recommendation: " + RESOLUTION_MAP["Unknown"]

if __name__ == "__main__":
    game_date_str = DATE.replace("-", "")
    game_info = get_game_info(game_date_str)
    result = resolve_market(game_info)
    print(result)