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
HOME_TEAM = "Angels"
AWAY_TEAM = "Yankees"

# Resolution map
RESOLUTION_MAP = {
    "Angels": "p1",
    "Yankees": "p2",
    "50-50": "p3",
    "Too early to resolve": "p4"
}

def get_data(url, headers):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

def find_game(games, home_team, away_team):
    for game in games:
        if game['HomeTeam'] == home_team and game['AwayTeam'] == away_team:
            return game
    return None

def resolve_market(game):
    if not game:
        return RESOLUTION_MAP["Too early to resolve"]
    if game['Status'] == 'Final':
        home_score = game['HomeTeamRuns']
        away_score = game['AwayTeamRuns']
        if home_score > away_score:
            return RESOLUTION_MAP[HOME_TEAM]
        elif away_score > home_score:
            return RESOLUTION_MAP[AWAY_TEAM]
    elif game['Status'] in ['Canceled', 'Postponed']:
        return RESOLUTION_MAP["50-50"]
    return RESOLUTION_MAP["Too early to resolve"]

def main():
    date_formatted = datetime.strptime(GAME_DATE, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = f"{PRIMARY_ENDPOINT}/GamesByDate/{date_formatted}"
    games = get_data(url, HEADERS)
    if games is None:
        print("Failed to retrieve data from primary endpoint, trying proxy...")
        games = get_data(PROXY_ENDPOINT, HEADERS)
        if games is None:
            print("Failed to retrieve data from both primary and proxy endpoints.")
            return

    game = find_game(games, HOME_TEAM, AWAY_TEAM)
    result = resolve_market(game)
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()