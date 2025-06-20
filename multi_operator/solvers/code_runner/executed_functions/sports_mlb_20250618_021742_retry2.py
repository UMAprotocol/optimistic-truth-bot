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
    "Twins": "p2",
    "Reds": "p1",
    "50-50": "p3",
    "Too early to resolve": "p4"
}

def get_data(url, proxy=False):
    endpoint = PROXY_ENDPOINT if proxy else PRIMARY_ENDPOINT
    try:
        response = requests.get(f"{endpoint}{url}", headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if proxy:
            print("Proxy failed, trying primary endpoint.")
            return get_data(url, proxy=False)
        else:
            print(f"Failed to retrieve data: {e}")
            return None

def find_game(date, home_team, away_team):
    games = get_data(f"/GamesByDate/{date}")
    if games:
        for game in games:
            if game['HomeTeam'] == home_team and game['AwayTeam'] == away_team:
                return game
    return None

def resolve_market(game):
    if not game:
        return RESOLUTION_MAP["Too early to resolve"]
    if game['Status'] == 'Final':
        home_runs = game['HomeTeamRuns']
        away_runs = game['AwayTeamRuns']
        if home_runs > away_runs:
            return RESOLUTION_MAP[game['HomeTeam']]
        elif away_runs > home_runs:
            return RESOLUTION_MAP[game['AwayTeam']]
    elif game['Status'] in ['Canceled', 'Postponed']:
        return RESOLUTION_MAP["50-50"]
    return RESOLUTION_MAP["Too early to resolve"]

def main():
    date = "2025-06-17"
    home_team = "Reds"
    away_team = "Twins"
    game = find_game(date, home_team, away_team)
    result = resolve_market(game)
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()