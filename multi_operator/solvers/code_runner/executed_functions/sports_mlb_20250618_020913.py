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
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-proxy/mlb"

# Game details
GAME_DATE = "2025-06-17"
HOME_TEAM = "Toronto Blue Jays"
AWAY_TEAM = "Arizona Diamondbacks"

# Resolution map
RESOLUTION_MAP = {
    "Blue Jays": "p1",
    "Diamondbacks": "p2",
    "50-50": "p3",
    "Too early to resolve": "p4"
}

def get_data(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
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
    if game['Status'] == "Final":
        if game['HomeTeamRuns'] > game['AwayTeamRuns']:
            return RESOLUTION_MAP[HOME_TEAM]
        elif game['HomeTeamRuns'] < game['AwayTeamRuns']:
            return RESOLUTION_MAP[AWAY_TEAM]
    elif game['Status'] in ["Canceled", "Postponed"]:
        return RESOLUTION_MAP["50-50"]
    return RESOLUTION_MAP["Too early to resolve"]

def main():
    # Try proxy endpoint first
    games = get_data(f"{PROXY_ENDPOINT}/GamesByDate/{GAME_DATE}")
    if not games:
        # Fallback to primary endpoint
        games = get_data(f"{PRIMARY_ENDPOINT}/GamesByDate/{GAME_DATE}")
    
    if games:
        game = find_game(games, HOME_TEAM, AWAY_TEAM)
        result = resolve_market(game)
        print(f"recommendation: {result}")
    else:
        print("recommendation:", RESOLUTION_MAP["Too early to resolve"])

if __name__ == "__main__":
    main()