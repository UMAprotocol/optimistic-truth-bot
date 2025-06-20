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
GAME_DATE = "2025-06-15"
HOME_TEAM = "Guardians"
AWAY_TEAM = "Mariners"

# Resolution map
RESOLUTION_MAP = {
    "Guardians": "p2",
    "Mariners": "p1",
    "50-50": "p3",
    "Too early to resolve": "p4"
}

def get_game_data(date, home_team, away_team):
    url = f"{PRIMARY_ENDPOINT}/GamesByDate/{date}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            games = response.json()
            for game in games:
                if game['HomeTeam'] == home_team and game['AwayTeam'] == away_team:
                    return game
        else:
            raise Exception("Failed to fetch data from primary endpoint")
    except requests.exceptions.RequestException:
        # Fallback to proxy endpoint
        proxy_url = f"{PROXY_ENDPOINT}/GamesByDate/{date}"
        response = requests.get(proxy_url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            games = response.json()
            for game in games:
                if game['HomeTeam'] == home_team and game['AwayTeam'] == away_team:
                    return game
        else:
            raise Exception("Failed to fetch data from proxy endpoint")
    return None

def resolve_market(game):
    if not game:
        return RESOLUTION_MAP["Too early to resolve"]
    if game['Status'] == "Final":
        if game['HomeTeamRuns'] > game['AwayTeamRuns']:
            return RESOLUTION_MAP[game['HomeTeam']]
        elif game['AwayTeamRuns'] > game['HomeTeamRuns']:
            return RESOLUTION_MAP[game['AwayTeam']]
    elif game['Status'] in ["Canceled", "Postponed"]:
        return RESOLUTION_MAP["50-50"]
    return RESOLUTION_MAP["Too early to resolve"]

if __name__ == "__main__":
    game_info = get_game_data(GAME_DATE, HOME_TEAM, AWAY_TEAM)
    result = resolve_market(game_info)
    print("recommendation:", result)