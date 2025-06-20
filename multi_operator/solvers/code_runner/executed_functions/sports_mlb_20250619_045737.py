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
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

# Game details
GAME_DATE = "2025-06-18"
HOME_TEAM = "Athletics"
AWAY_TEAM = "Astros"

# Resolution map
RESOLUTION_MAP = {
    "Astros": "p2",
    "Athletics": "p1",
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

def resolve_market(games, home_team, away_team):
    if games is None:
        return "recommendation: p4"  # Unable to fetch data

    for game in games:
        if game['HomeTeam'] == home_team and game['AwayTeam'] == away_team:
            if game['Status'] == "Final":
                home_score = game['HomeTeamRuns']
                away_score = game['AwayTeamRuns']
                if home_score > away_score:
                    return f"recommendation: {RESOLUTION_MAP[home_team]}"
                elif away_score > home_score:
                    return f"recommendation: {RESOLUTION_MAP[away_team]}"
            elif game['Status'] == "Postponed":
                return f"recommendation: {RESOLUTION_MAP['Postponed']}"
            elif game['Status'] == "Canceled":
                return f"recommendation: {RESOLUTION_MAP['Canceled']}"
    return "recommendation: p4"  # Game not found or in progress

if __name__ == "__main__":
    games = get_game_data(GAME_DATE)
    result = resolve_market(games, HOME_TEAM, AWAY_TEAM)
    print(result)