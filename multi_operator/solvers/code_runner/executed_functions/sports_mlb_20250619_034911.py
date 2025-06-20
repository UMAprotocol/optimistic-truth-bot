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
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/mlb-proxy"

# Game details
GAME_DATE = "2025-06-18"
HOME_TEAM = "CIN"  # Cincinnati Reds
AWAY_TEAM = "MIN"  # Minnesota Twins

# Resolution map
RESOLUTION_MAP = {
    "CIN": "p1",  # Reds win
    "MIN": "p2",  # Twins win
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
    except requests.RequestException:
        try:
            # Fallback to proxy endpoint
            response = requests.get(f"{PROXY_ENDPOINT}/GamesByDate/{date}", headers=HEADERS, timeout=10)
            response.raise_for_status()
            games = response.json()
            for game in games:
                if game['HomeTeam'] == HOME_TEAM and game['AwayTeam'] == AWAY_TEAM:
                    return game
        except requests.RequestException:
            return None
    return None

def resolve_market(game):
    if not game:
        return "recommendation: p4"  # Unable to retrieve game data
    status = game['Status']
    if status in ["Postponed", "Canceled"]:
        return f"recommendation: {RESOLUTION_MAP[status]}"
    elif status == "Final":
        home_score = game['HomeTeamRuns']
        away_score = game['AwayTeamRuns']
        if home_score > away_score:
            return f"recommendation: {RESOLUTION_MAP[HOME_TEAM]}"
        elif away_score > home_score:
            return f"recommendation: {RESOLUTION_MAP[AWAY_TEAM]}"
    return f"recommendation: {RESOLUTION_MAP['Scheduled']}"

if __name__ == "__main__":
    game_info = get_game_data(GAME_DATE)
    result = resolve_market(game_info)
    print(result)