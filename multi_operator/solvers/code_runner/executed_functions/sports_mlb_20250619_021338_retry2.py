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
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/mlb-proxy"

# Resolution map
RESOLUTION_MAP = {
    "Angels": "p2",
    "Yankees": "p1",
    "50-50": "p3",
    "Too early to resolve": "p4"
}

def get_game_data(date, home_team, away_team):
    formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = f"{PRIMARY_ENDPOINT}/GamesByDate/{formatted_date}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        games = response.json()
        for game in games:
            if game['HomeTeam'] == home_team and game['AwayTeam'] == away_team:
                return game
    except requests.exceptions.RequestException as e:
        print(f"Primary endpoint failed, trying proxy. Error: {e}")
        proxy_url = f"{PROXY_ENDPOINT}/GamesByDate/{formatted_date}"
        response = requests.get(proxy_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        games = response.json()
        for game in games:
            if game['HomeTeam'] == home_team and game['AwayTeam'] == away_team:
                return game
    return None

def resolve_market(game):
    if not game:
        return RESOLUTION_MAP["Too early to resolve"]
    if game['Status'] == 'Final':
        if game['HomeTeamRuns'] > game['AwayTeamRuns']:
            return RESOLUTION_MAP[game['HomeTeam']]
        elif game['HomeTeamRuns'] < game['AwayTeamRuns']:
            return RESOLUTION_MAP[game['AwayTeam']]
    elif game['Status'] == 'Canceled':
        return RESOLUTION_MAP["50-50"]
    elif game['Status'] == 'Postponed':
        return RESOLUTION_MAP["Too early to resolve"]
    return RESOLUTION_MAP["Too early to resolve"]

if __name__ == "__main__":
    game_date = "2025-06-18"
    home_team = "Yankees"
    away_team = "Angels"
    game = get_game_data(game_date, home_team, away_team)
    recommendation = resolve_market(game)
    print(f"recommendation: {recommendation}")