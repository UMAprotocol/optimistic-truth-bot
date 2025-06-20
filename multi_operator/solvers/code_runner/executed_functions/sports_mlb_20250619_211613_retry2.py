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
    "Cardinals": "p2",
    "White Sox": "p1",
    "Postponed": "p4",
    "Canceled": "p3",
    "50-50": "p3"
}

def get_game_data(date, team1, team2):
    url = f"{PRIMARY_ENDPOINT}/GamesByDate/{date}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        games = response.json()
        for game in games:
            if (game['HomeTeam'] == team1 and game['AwayTeam'] == team2) or \
               (game['HomeTeam'] == team2 and game['AwayTeam'] == team1):
                return game
    except requests.exceptions.RequestException:
        # Fallback to proxy endpoint
        proxy_url = f"{PROXY_ENDPOINT}/GamesByDate/{date}"
        response = requests.get(proxy_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        games = response.json()
        for game in games:
            if (game['HomeTeam'] == team1 and game['AwayTeam'] == team2) or \
               (game['HomeTeam'] == team2 and game['AwayTeam'] == team1):
                return game
    return None

def resolve_market(game):
    if not game:
        return "recommendation: p4"
    if game['Status'] == "Final":
        if game['HomeTeamRuns'] > game['AwayTeamRuns']:
            return f"recommendation: {RESOLUTION_MAP[game['HomeTeam']]}"
        else:
            return f"recommendation: {RESOLUTION_MAP[game['AwayTeam']]}"
    elif game['Status'] == "Postponed":
        return "recommendation: p4"
    elif game['Status'] == "Canceled":
        return "recommendation: p3"
    return "recommendation: p4"

if __name__ == "__main__":
    # Game details
    game_date = "2025-06-19"
    home_team = "White Sox"
    away_team = "Cardinals"

    # Get game data
    game = get_game_data(game_date, home_team, away_team)

    # Resolve market based on game data
    result = resolve_market(game)
    print(result)