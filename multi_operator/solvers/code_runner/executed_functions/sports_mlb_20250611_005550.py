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
GAME_DATE = "2025-06-10"
HOME_TEAM = "Cincinnati Reds"
AWAY_TEAM = "Cleveland Guardians"

# Resolution map
RESOLUTION_MAP = {
    HOME_TEAM: "p2",
    AWAY_TEAM: "p1",
    "Postponed": "p4",
    "Canceled": "p3",
    "50-50": "p3"
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
            response = requests.get(f"{PROXY_ENDPOINT}/GamesByDate/{date}", headers=HEADERS, timeout=10)
            response.raise_for_status()
            games = response.json()
            return games
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data from proxy endpoint: {e}")
            return None

def resolve_market(games):
    for game in games:
        if game['HomeTeam'] == HOME_TEAM and game['AwayTeam'] == AWAY_TEAM:
            if game['Status'] == "Final":
                if game['HomeTeamRuns'] > game['AwayTeamRuns']:
                    return "recommendation: " + RESOLUTION_MAP[HOME_TEAM]
                elif game['AwayTeamRuns'] > game['HomeTeamRuns']:
                    return "recommendation: " + RESOLUTION_MAP[AWAY_TEAM]
            elif game['Status'] == "Postponed":
                return "recommendation: " + RESOLUTION_MAP["Postponed"]
            elif game['Status'] == "Canceled":
                return "recommendation: " + RESOLUTION_MAP["Canceled"]
    return "recommendation: p4"

if __name__ == "__main__":
    games = get_game_data(GAME_DATE)
    if games:
        result = resolve_market(games)
        print(result)
    else:
        print("recommendation: p4")