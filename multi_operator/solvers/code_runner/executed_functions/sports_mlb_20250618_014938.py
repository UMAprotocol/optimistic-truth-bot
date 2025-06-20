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
GAME_DATE = "2025-06-17"
HOME_TEAM = "Nationals"
AWAY_TEAM = "Rockies"

# Resolution map
RESOLUTION_MAP = {
    "Nationals": "p1",
    "Rockies": "p2",
    "Postponed": "p3",
    "Canceled": "p3",
    "Unknown": "p3"
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
        return "p3"  # Unknown or no game found
    if game['Status'] == "Final":
        if game['HomeTeamRuns'] > game['AwayTeamRuns']:
            return RESOLUTION_MAP[game['HomeTeam']]
        elif game['HomeTeamRuns'] < game['AwayTeamRuns']:
            return RESOLUTION_MAP[game['AwayTeam']]
    elif game['Status'] in ["Postponed", "Canceled"]:
        return RESOLUTION_MAP[game['Status']]
    return "p3"  # Default to unknown for other statuses

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
        print("recommendation: p3")  # Unknown or API failure

if __name__ == "__main__":
    main()