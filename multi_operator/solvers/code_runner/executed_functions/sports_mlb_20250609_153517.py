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
GAME_DATE = "2025-05-28"
TEAM1 = "Cincinnati Reds"
TEAM2 = "Kansas City Royals"

# Resolution map
RESOLUTION_MAP = {
    TEAM1: "p2",  # Cincinnati Reds win
    TEAM2: "p1",  # Kansas City Royals win
    "Postponed": "p4",  # Game postponed
    "Canceled": "p3",  # Game canceled
    "Unknown": "p4"  # Unknown or in-progress
}

def get_game_data(date):
    url = f"{PRIMARY_ENDPOINT}/GamesByDate/{date}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from primary endpoint: {e}")
        try:
            response = requests.get(f"{PROXY_ENDPOINT}/mlb/GamesByDate/{date}", timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data from proxy endpoint: {e}")
            return None

def analyze_game_results(games):
    for game in games:
        if {game['HomeTeam'], game['AwayTeam']} == {TEAM1, TEAM2}:
            if game['Status'] == "Final":
                if game['HomeTeamRuns'] > game['AwayTeamRuns']:
                    winner = game['HomeTeam']
                else:
                    winner = game['AwayTeam']
                return RESOLUTION_MAP.get(winner, "Unknown")
            else:
                return RESOLUTION_MAP.get(game['Status'], "Unknown")
    return "Unknown"

if __name__ == "__main__":
    games = get_game_data(GAME_DATE)
    if games:
        result = analyze_game_results(games)
        print(f"recommendation: {RESOLUTION_MAP.get(result, 'Unknown')}")
    else:
        print("recommendation: p4")  # Unable to retrieve data