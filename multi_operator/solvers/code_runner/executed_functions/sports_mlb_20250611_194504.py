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
GAME_DATE = "2025-06-11"
HOME_TEAM = "PHI"  # Philadelphia Phillies
AWAY_TEAM = "CHC"  # Chicago Cubs

# Resolution map
RESOLUTION_MAP = {
    HOME_TEAM: "p1",  # Phillies win
    AWAY_TEAM: "p2",  # Cubs win
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
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from primary endpoint: {e}")
        try:
            response = requests.get(f"{PROXY_ENDPOINT}/mlb/GamesByDate/{date}", timeout=10)
            response.raise_for_status()
            games = response.json()
            for game in games:
                if game['HomeTeam'] == HOME_TEAM and game['AwayTeam'] == AWAY_TEAM:
                    return game
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data from proxy endpoint: {e}")
    return None

def resolve_market(game):
    if not game:
        return "recommendation: p4"  # No data available
    status = game['Status']
    if status in ["Final", "Game Over"]:
        home_runs = game['HomeTeamRuns']
        away_runs = game['AwayTeamRuns']
        if home_runs > away_runs:
            return f"recommendation: {RESOLUTION_MAP[HOME_TEAM]}"
        elif away_runs > home_runs:
            return f"recommendation: {RESOLUTION_MAP[AWAY_TEAM]}"
        else:
            return "recommendation: p3"  # Tie or error in data
    return f"recommendation: {RESOLUTION_MAP.get(status, 'p4')}"

if __name__ == "__main__":
    game_info = get_game_data(GAME_DATE)
    result = resolve_market(game_info)
    print(result)