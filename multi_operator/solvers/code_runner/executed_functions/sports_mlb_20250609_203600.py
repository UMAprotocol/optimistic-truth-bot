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
GAME_DATE = "2025-05-31"
HOME_TEAM = "Yankees"
AWAY_TEAM = "Dodgers"

# Resolution map
RESOLUTION_MAP = {
    "Yankees": "p2",
    "Dodgers": "p1",
    "Postponed": "p4",
    "Canceled": "p3",
    "Unknown": "p3"
}

def get_game_data(date):
    url = f"{PRIMARY_ENDPOINT}/GamesByDate/{date}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        games = response.json()
        return games
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from primary endpoint: {e}")
        try:
            response = requests.get(f"{PROXY_ENDPOINT}/GamesByDate/{date}", timeout=10)
            response.raise_for_status()
            games = response.json()
            return games
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data from proxy endpoint: {e}")
            return None

def resolve_market(games):
    if games is None:
        return "recommendation: p4"  # Unable to fetch data

    for game in games:
        if game['HomeTeam'] == HOME_TEAM and game['AwayTeam'] == AWAY_TEAM:
            if game['Status'] == "Final":
                if game['HomeTeamRuns'] > game['AwayTeamRuns']:
                    return f"recommendation: {RESOLUTION_MAP[HOME_TEAM]}"
                elif game['HomeTeamRuns'] < game['AwayTeamRuns']:
                    return f"recommendation: {RESOLUTION_MAP[AWAY_TEAM]}"
            elif game['Status'] == "Postponed":
                return f"recommendation: {RESOLUTION_MAP['Postponed']}"
            elif game['Status'] == "Canceled":
                return f"recommendation: {RESOLUTION_MAP['Canceled']}"
    return "recommendation: p4"  # No matching game found or game not yet played

if __name__ == "__main__":
    games = get_game_data(GAME_DATE)
    result = resolve_market(games)
    print(result)