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
HOME_TEAM = "Yankees"
AWAY_TEAM = "Angels"

# Resolution map
RESOLUTION_MAP = {
    "Yankees": "p1",
    "Angels": "p2",
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
        return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]
    if game['Status'] == 'Final':
        if game['HomeTeamRuns'] > game['AwayTeamRuns']:
            return "recommendation: " + RESOLUTION_MAP[game['HomeTeam']]
        elif game['HomeTeamRuns'] < game['AwayTeamRuns']:
            return "recommendation: " + RESOLUTION_MAP[game['AwayTeam']]
    elif game['Status'] in ['Canceled', 'Postponed']:
        return "recommendation: " + RESOLUTION_MAP["50-50"]
    return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

def main():
    # Construct URL for the game date
    url = f"{PRIMARY_ENDPOINT}/GamesByDate/{GAME_DATE}"
    games_data = get_data(url, HEADERS)
    if not games_data:
        print("Failed to retrieve data from primary endpoint, trying proxy...")
        games_data = get_data(PROXY_ENDPOINT, HEADERS)
        if not games_data:
            print("Failed to retrieve data from both primary and proxy endpoints.")
            return

    # Find the specific game
    game = find_game(games_data, HOME_TEAM, AWAY_TEAM)
    # Resolve the market based on the game data
    result = resolve_market(game)
    print(result)

if __name__ == "__main__":
    main()