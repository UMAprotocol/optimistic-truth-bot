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
GAME_DATE = "2025-06-10"
TEAM1 = "Detroit Tigers"
TEAM2 = "Baltimore Orioles"

# Resolution map
RESOLUTION_MAP = {
    "Tigers": "p2",
    "Orioles": "p1",
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

def find_game(games, team1, team2):
    for game in games:
        if (game['HomeTeam'] == team1 and game['AwayTeam'] == team2) or \
           (game['HomeTeam'] == team2 and game['AwayTeam'] == team1):
            return game
    return None

def resolve_market(game):
    if not game:
        return RESOLUTION_MAP["Too early to resolve"]
    if game['Status'] == "Final":
        if game['HomeTeamRuns'] > game['AwayTeamRuns']:
            winner = game['HomeTeam']
        else:
            winner = game['AwayTeam']
        return RESOLUTION_MAP[winner]
    elif game['Status'] == "Canceled":
        return RESOLUTION_MAP["50-50"]
    elif game['Status'] == "Postponed":
        return RESOLUTION_MAP["Too early to resolve"]
    else:
        return RESOLUTION_MAP["Too early to resolve"]

def main():
    # Fetch games for the specified date
    games_url = f"{PRIMARY_ENDPOINT}/GamesByDate/{GAME_DATE}"
    games = get_data(games_url, HEADERS)
    if not games:
        # Fallback to proxy if primary fails
        games = get_data(PROXY_ENDPOINT, HEADERS)
    
    if games:
        game = find_game(games, TEAM1, TEAM2)
        result = resolve_market(game)
    else:
        result = RESOLUTION_MAP["Too early to resolve"]
    
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()