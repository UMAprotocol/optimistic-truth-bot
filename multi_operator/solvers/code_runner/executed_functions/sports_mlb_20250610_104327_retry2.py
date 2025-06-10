import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
MLB_API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not MLB_API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# API configuration
HEADERS = {"Ocp-Apim-Subscription-Key": MLB_API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/mlb/scores/json"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-proxy/mlb"

# Game details
GAME_DATE = "2025-06-09"
HOME_TEAM = "Angels"
AWAY_TEAM = "Athletics"

# Resolution map
RESOLUTION_MAP = {
    "Angels": "p1",
    "Athletics": "p2",
    "Postponed": "p4",
    "Canceled": "p3"
}

def get_game_data(date):
    # Try proxy endpoint first
    url = f"{PROXY_ENDPOINT}/GamesByDate/{date}"
    response = requests.get(url, headers=HEADERS, timeout=10)
    if not response.ok:
        # Fallback to primary endpoint
        url = f"{PRIMARY_ENDPOINT}/GamesByDate/{date}"
        response = requests.get(url, headers=HEADERS, timeout=10)
    return response.json()

def analyze_game_results(games):
    for game in games:
        if game["HomeTeam"] == HOME_TEAM and game["AwayTeam"] == AWAY_TEAM:
            if game["Status"] == "Final":
                home_score = game["HomeTeamRuns"]
                away_score = game["AwayTeamRuns"]
                if home_score > away_score:
                    return RESOLUTION_MAP[HOME_TEAM]
                elif away_score > home_score:
                    return RESOLUTION_MAP[AWAY_TEAM]
            elif game["Status"] in ["Postponed", "Canceled"]:
                return RESOLUTION_MAP[game["Status"]]
    return "p4"  # If no relevant game found or in progress

def main():
    try:
        games = get_game_data(GAME_DATE)
        recommendation = analyze_game_results(games)
        print(f"recommendation: {recommendation}")
    except Exception as e:
        print(f"Error: {str(e)}")
        print("recommendation: p4")

if __name__ == "__main__":
    main()