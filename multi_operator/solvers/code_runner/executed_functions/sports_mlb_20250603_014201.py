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
GAME_DATE = "2025-06-02"
HOME_TEAM = "CIN"  # Cincinnati Reds
AWAY_TEAM = "MIL"  # Milwaukee Brewers

# Resolution map
RESOLUTION_MAP = {
    HOME_TEAM: "p1",  # Reds win
    AWAY_TEAM: "p2",  # Brewers win
    "Canceled": "p3",  # Game canceled
    "Postponed": "p4",  # Game postponed
    "Scheduled": "p4",  # Game not yet played
    "In Progress": "p4",  # Game in progress
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
        print(f"Error fetching data from primary endpoint: {e}")
        # Fallback to proxy
        try:
            response = requests.get(f"{PROXY_ENDPOINT}/GamesByDate/{date}", headers=HEADERS, timeout=10)
            response.raise_for_status()
            games = response.json()
            for game in games:
                if game['HomeTeam'] == HOME_TEAM and game['AwayTeam'] == AWAY_TEAM:
                    return game
            return None
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data from proxy endpoint: {e}")
            return None

def resolve_market(game):
    if not game:
        return "recommendation: p4"  # No game data found
    status = game.get('Status')
    if status in ["Final", "Game Over"]:
        home_score = game.get('HomeTeamRuns')
        away_score = game.get('AwayTeamRuns')
        if home_score > away_score:
            return f"recommendation: {RESOLUTION_MAP[HOME_TEAM]}"
        elif away_score > home_score:
            return f"recommendation: {RESOLUTION_MAP[AWAY_TEAM]}"
    return f"recommendation: {RESOLUTION_MAP.get(status, 'p4')}"

if __name__ == "__main__":
    game_date_str = datetime.strptime(GAME_DATE, "%Y-%m-%d").strftime("%Y-%m-%d")
    game_info = get_game_data(game_date_str)
    result = resolve_market(game_info)
    print(result)