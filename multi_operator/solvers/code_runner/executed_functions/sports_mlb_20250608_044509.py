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
GAME_DATE = "2025-06-07"
HOME_TEAM = "Angels"
AWAY_TEAM = "Mariners"

# Resolution map
RESOLUTION_MAP = {
    "Angels": "p1",
    "Mariners": "p2",
    "50-50": "p3",
    "Too early to resolve": "p4"
}

def get_game_data(date, home_team, away_team):
    url = f"{PRIMARY_ENDPOINT}/GamesByDate/{date}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        games = response.json()
        for game in games:
            if game['HomeTeam'] == home_team and game['AwayTeam'] == away_team:
                return game
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from primary endpoint: {e}")
        try:
            response = requests.get(f"{PROXY_ENDPOINT}/mlb/GamesByDate/{date}", timeout=10)
            response.raise_for_status()
            games = response.json()
            for game in games:
                if game['HomeTeam'] == home_team and game['AwayTeam'] == away_team:
                    return game
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data from proxy endpoint: {e}")
    return None

def resolve_market(game):
    if not game:
        return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]
    if game['Status'] == "Final":
        if game['HomeTeamRuns'] > game['AwayTeamRuns']:
            return "recommendation: " + RESOLUTION_MAP[game['HomeTeam']]
        elif game['AwayTeamRuns'] > game['HomeTeamRuns']:
            return "recommendation: " + RESOLUTION_MAP[game['AwayTeam']]
    elif game['Status'] in ["Canceled", "Postponed"]:
        return "recommendation: " + RESOLUTION_MAP["50-50"]
    return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

if __name__ == "__main__":
    game_info = get_game_data(GAME_DATE, HOME_TEAM, AWAY_TEAM)
    result = resolve_market(game_info)
    print(result)