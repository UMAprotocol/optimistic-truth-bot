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
GAME_DATE = "2025-06-16"
PHILLIES_KEY = "PHI"
MARLINS_KEY = "MIA"

# Resolution map
RESOLUTION_MAP = {
    "PHI": "p2",  # Phillies win
    "MIA": "p1",  # Marlins win
    "Postponed": "p4",  # Game postponed
    "Canceled": "p3",  # Game canceled
    "Scheduled": "p4"  # Game scheduled but not played yet
}

def get_game_data(date):
    url = f"{PRIMARY_ENDPOINT}/GamesByDate/{date}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        games = response.json()
        for game in games:
            if {game["HomeTeam"], game["AwayTeam"]} == {PHILLIES_KEY, MARLINS_KEY}:
                return game
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from primary endpoint: {e}")
        # Fallback to proxy
        try:
            proxy_url = f"{PROXY_ENDPOINT}/mlb/scores/json/GamesByDate/{date}"
            response = requests.get(proxy_url, headers=HEADERS, timeout=10)
            response.raise_for_status()
            games = response.json()
            for game in games:
                if {game["HomeTeam"], game["AwayTeam"]} == {PHILLIES_KEY, MARLINS_KEY}:
                    return game
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data from proxy endpoint: {e}")
    return None

def resolve_market(game):
    if not game:
        return "recommendation: p4"  # No data available
    if game["Status"] == "Final":
        if game["HomeTeamRuns"] > game["AwayTeamRuns"]:
            winner = game["HomeTeam"]
        else:
            winner = game["AwayTeam"]
        return f"recommendation: {RESOLUTION_MAP[winner]}"
    else:
        return f"recommendation: {RESOLUTION_MAP[game['Status']]}"

if __name__ == "__main__":
    game_info = get_game_data(GAME_DATE)
    result = resolve_market(game_info)
    print(result)