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
GAME_DATE = "2025-06-18"
HOME_TEAM = "Texas Rangers"
AWAY_TEAM = "Kansas City Royals"

# Resolution map
RESOLUTION_MAP = {
    HOME_TEAM: "p1",
    AWAY_TEAM: "p2",
    "Canceled": "p3",
    "Postponed": "p4",
    "In Progress": "p4"
}

def get_game_data(date, home_team, away_team):
    url = f"{PRIMARY_ENDPOINT}/GamesByDate/{date}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        games = response.json()
        for game in games:
            if game["HomeTeam"] == home_team and game["AwayTeam"] == away_team:
                return game
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from primary endpoint: {e}")
        try:
            response = requests.get(f"{PROXY_ENDPOINT}/GamesByDate/{date}", timeout=10)
            response.raise_for_status()
            games = response.json()
            for game in games:
                if game["HomeTeam"] == home_team and game["AwayTeam"] == away_team:
                    return game
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data from proxy endpoint: {e}")
    return None

def resolve_market(game):
    if not game:
        return "recommendation: p4"
    if game["Status"] == "Final":
        if game["HomeTeamRuns"] > game["AwayTeamRuns"]:
            return f"recommendation: {RESOLUTION_MAP[HOME_TEAM]}"
        elif game["HomeTeamRuns"] < game["AwayTeamRuns"]:
            return f"recommendation: {RESOLUTION_MAP[AWAY_TEAM]}"
    elif game["Status"] in ["Canceled", "Postponed"]:
        return f"recommendation: {RESOLUTION_MAP[game['Status']]}"
    return "recommendation: p4"

if __name__ == "__main__":
    game_info = get_game_data(GAME_DATE, HOME_TEAM, AWAY_TEAM)
    result = resolve_market(game_info)
    print(result)