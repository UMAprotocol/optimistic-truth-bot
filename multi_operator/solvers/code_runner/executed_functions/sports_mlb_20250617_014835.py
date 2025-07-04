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
HOME_TEAM = "Orioles"
AWAY_TEAM = "Rays"

# Resolution map
RESOLUTION_MAP = {
    HOME_TEAM: "p2",
    AWAY_TEAM: "p1",
    "Postponed": "p4",
    "Canceled": "p3",
    "50-50": "p3"
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
        return "p4"  # Game not found, too early to resolve
    if game['Status'] == "Final":
        if game['HomeTeamRuns'] > game['AwayTeamRuns']:
            return RESOLUTION_MAP[HOME_TEAM]
        elif game['AwayTeamRuns'] > game['HomeTeamRuns']:
            return RESOLUTION_MAP[AWAY_TEAM]
    elif game['Status'] == "Canceled":
        return RESOLUTION_MAP["Canceled"]
    elif game['Status'] == "Postponed":
        return RESOLUTION_MAP["Postponed"]
    return "p4"

def main():
    # Construct URL for the game date
    url = f"{PRIMARY_ENDPOINT}/GamesByDate/{GAME_DATE}"
    games = get_data(url, HEADERS)
    if not games:
        print("Failed to retrieve games data.")
        return

    # Find the specific game
    game = find_game(games, HOME_TEAM, AWAY_TEAM)
    if not game:
        print("Game not found on the specified date.")
        return

    # Resolve the market based on the game outcome
    recommendation = resolve_market(game)
    print(f"recommendation: {recommendation}")

if __name__ == "__main__":
    main()