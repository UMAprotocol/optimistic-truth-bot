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
HOME_TEAM = "San Diego Padres"
AWAY_TEAM = "Los Angeles Dodgers"

# Resolution map
RESOLUTION_MAP = {
    HOME_TEAM: "p1",
    AWAY_TEAM: "p2",
    "Postponed": "p4",
    "Canceled": "p3",
    "Final": "final"
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

def analyze_game(games):
    for game in games:
        if game['HomeTeam'] == HOME_TEAM and game['AwayTeam'] == AWAY_TEAM:
            game_status = game['Status']
            if game_status in ["Final", "Postponed", "Canceled"]:
                return RESOLUTION_MAP.get(game_status, "p4")
            elif game_status == "Final":
                home_score = game['HomeTeamRuns']
                away_score = game['AwayTeamRuns']
                if home_score > away_score:
                    return RESOLUTION_MAP[HOME_TEAM]
                elif away_score > home_score:
                    return RESOLUTION_MAP[AWAY_TEAM]
    return "p4"

def main():
    games = get_game_data(GAME_DATE)
    if games:
        result = analyze_game(games)
        print(f"recommendation: {result}")
    else:
        print("recommendation: p4")

if __name__ == "__main__":
    main()