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
GAME_DATE = "2025-05-26"
HOME_TEAM = "Angels"
AWAY_TEAM = "Yankees"

# Resolution map
RESOLUTION_MAP = {
    "Angels": "p1",
    "Yankees": "p2",
    "Postponed": "p4",
    "Canceled": "p3",
    "Unknown": "p3"
}

def get_game_data(date):
    url = f"{PRIMARY_ENDPOINT}/GamesByDate/{date}"
    proxy_url = f"{PROXY_ENDPOINT}/GamesByDate/{date}"
    try:
        response = requests.get(proxy_url, headers=HEADERS, timeout=10)
        if not response.ok:
            raise Exception("Proxy failed")
    except:
        response = requests.get(url, headers=HEADERS, timeout=10)
    if response.ok:
        return response.json()
    return None

def analyze_game_results(games):
    for game in games:
        if game['HomeTeam'] == HOME_TEAM and game['AwayTeam'] == AWAY_TEAM:
            if game['Status'] == "Final":
                home_score = game['HomeTeamRuns']
                away_score = game['AwayTeamRuns']
                if home_score > away_score:
                    return RESOLUTION_MAP[HOME_TEAM]
                elif away_score > home_score:
                    return RESOLUTION_MAP[AWAY_TEAM]
            elif game['Status'] in ["Postponed", "Canceled"]:
                return RESOLUTION_MAP[game['Status']]
    return RESOLUTION_MAP["Unknown"]

def main():
    games = get_game_data(GAME_DATE)
    if games:
        result = analyze_game_results(games)
        print(f"recommendation: {result}")
    else:
        print("recommendation: p4")  # No data available

if __name__ == "__main__":
    main()