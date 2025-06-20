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
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/binance-proxy/mlb"

# Game details
GAME_DATE = "2025-06-10"
HOME_TEAM = "Arizona Diamondbacks"
AWAY_TEAM = "Seattle Mariners"

# Resolution map
RESOLUTION_MAP = {
    HOME_TEAM: "p1",
    AWAY_TEAM: "p2",
    "Canceled": "p3",
    "Postponed": "p4",
    "In Progress": "p4"
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
        return "p4"  # Game not found, cannot resolve yet
    if game['Status'] == "Final":
        if game['HomeTeamRuns'] > game['AwayTeamRuns']:
            return RESOLUTION_MAP[HOME_TEAM]
        elif game['AwayTeamRuns'] > game['HomeTeamRuns']:
            return RESOLUTION_MAP[AWAY_TEAM]
    return RESOLUTION_MAP.get(game['Status'], "p4")

def main():
    # Construct URL for the game date
    url = f"{PRIMARY_ENDPOINT}/GamesByDate/{GAME_DATE}"
    games = get_data(url, HEADERS)
    if not games:
        # Try proxy if primary fails
        url = f"{PROXY_ENDPOINT}/GamesByDate/{GAME_DATE}"
        games = get_data(url, HEADERS)
        if not games:
            return "p4"  # Unable to fetch data

    # Find the specific game
    game = find_game(games, HOME_TEAM, AWAY_TEAM)
    # Resolve the market based on the game data
    result = resolve_market(game)
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()