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
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-proxy/mlb/scores/json"

# Game details
GAME_DATE = "2025-05-29"
HOME_TEAM = "Astros"
AWAY_TEAM = "Rays"

# Resolution map
RESOLUTION_MAP = {
    HOME_TEAM: "p1",
    AWAY_TEAM: "p2",
    "Canceled": "p3",
    "Postponed": "p4",
    "Scheduled": "p4"
}

def get_data(endpoint, path):
    url = f"{endpoint}/{path}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from {url}: {e}")
        return None

def find_game(games, home_team, away_team):
    for game in games:
        if game['HomeTeam'] == home_team and game['AwayTeam'] == away_team:
            return game
    return None

def resolve_market(game):
    if not game:
        return "p4"  # Game not found, too early to resolve
    status = game.get("Status")
    if status in ["Final", "Game Over"]:
        home_runs = game.get("HomeTeamRuns", 0)
        away_runs = game.get("AwayTeamRuns", 0)
        if home_runs > away_runs:
            return RESOLUTION_MAP[HOME_TEAM]
        elif away_runs > home_runs:
            return RESOLUTION_MAP[AWAY_TEAM]
    return RESOLUTION_MAP.get(status, "p4")

def main():
    # Try proxy endpoint first
    games = get_data(PROXY_ENDPOINT, f"GamesByDate/{GAME_DATE}")
    if not games:
        # Fallback to primary endpoint
        games = get_data(PRIMARY_ENDPOINT, f"GamesByDate/{GAME_DATE}")
    
    if games:
        game = find_game(games, HOME_TEAM, AWAY_TEAM)
        result = resolve_market(game)
    else:
        result = "p4"  # Unable to fetch data

    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()