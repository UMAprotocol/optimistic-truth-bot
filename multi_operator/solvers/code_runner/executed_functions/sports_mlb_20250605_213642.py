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
GAME_DATE = "2025-06-05"
HOME_TEAM = "Blue Jays"
AWAY_TEAM = "Phillies"

# Resolution map
RESOLUTION_MAP = {
    "Blue Jays": "p1",
    "Phillies": "p2",
    "50-50": "p3",
    "Too early to resolve": "p4"
}

def get_data(url, params=None):
    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=10)
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
        return "Too early to resolve"
    if game['Status'] == 'Final':
        if game['HomeTeamRuns'] > game['AwayTeamRuns']:
            return HOME_TEAM
        elif game['HomeTeamRuns'] < game['AwayTeamRuns']:
            return AWAY_TEAM
    elif game['Status'] in ['Canceled', 'Postponed']:
        return "50-50"
    return "Too early to resolve"

def main():
    # Construct URL for the game date
    url = f"{PRIMARY_ENDPOINT}/GamesByDate/{GAME_DATE}"
    games = get_data(url)
    if not games:
        print("No games found or error in data retrieval.")
        return

    # Find the specific game
    game = find_game(games, HOME_TEAM, AWAY_TEAM)
    outcome = resolve_market(game)
    recommendation = RESOLUTION_MAP.get(outcome, "p4")
    print(f"recommendation: {recommendation}")

if __name__ == "__main__":
    main()