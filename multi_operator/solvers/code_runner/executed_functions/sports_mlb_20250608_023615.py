import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# API configuration
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/mlb/scores/json"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

# Game details
GAME_DATE = "2025-06-07"
HOME_TEAM = "BOS"  # Boston Red Sox
AWAY_TEAM = "NYY"  # New York Yankees

# Resolution map
RESOLUTION_MAP = {
    HOME_TEAM: "p2",  # Red Sox win
    AWAY_TEAM: "p1",  # Yankees win
    "Postponed": "p4",  # Game postponed
    "Canceled": "p3",  # Game canceled
    "Scheduled": "p4",  # Game scheduled but not yet played
    "Final": "p4"  # Game completed, determine winner
}

def get_game_data(date):
    url = f"{PRIMARY_ENDPOINT}/GamesByDate/{date}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        games = response.json()
        for game in games:
            if game['HomeTeam'] == HOME_TEAM and game['AwayTeam'] == AWAY_TEAM:
                return game
        return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching game data: {e}")
        return None

def resolve_market(game):
    if not game:
        return "p4"  # No game data found
    status = game['Status']
    if status == "Final":
        home_score = game['HomeTeamRuns']
        away_score = game['AwayTeamRuns']
        if home_score > away_score:
            return RESOLUTION_MAP[HOME_TEAM]
        elif away_score > home_score:
            return RESOLUTION_MAP[AWAY_TEAM]
        else:
            return "p3"  # Tie game, resolve as 50-50
    else:
        return RESOLUTION_MAP.get(status, "p4")

if __name__ == "__main__":
    game_info = get_game_data(GAME_DATE)
    recommendation = resolve_market(game_info)
    print(f"recommendation: {recommendation}")