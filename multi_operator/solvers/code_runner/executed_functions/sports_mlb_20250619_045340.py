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

# Resolution map based on the game outcome
RESOLUTION_MAP = {
    "Padres": "p2",
    "Dodgers": "p1",
    "Postponed": "p4",
    "Canceled": "p3",
    "Unknown": "p3"
}

def get_game_data(date, team1, team2):
    url = f"{PRIMARY_ENDPOINT}/GamesByDate/{date}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if not response.ok:
            # Fallback to proxy if primary fails
            response = requests.get(f"{PROXY_ENDPOINT}/GamesByDate/{date}", headers=HEADERS, timeout=10)
        games = response.json()
        for game in games:
            if (game['HomeTeam'] == team1 and game['AwayTeam'] == team2) or (game['HomeTeam'] == team2 and game['AwayTeam'] == team1):
                return game
    except requests.RequestException as e:
        print(f"Error fetching game data: {e}")
    return None

def resolve_market(game):
    if not game:
        return "recommendation: p4"  # No game data found
    if game['Status'] == "Final":
        if game['HomeTeamRuns'] > game['AwayTeamRuns']:
            winner = game['HomeTeam']
        else:
            winner = game['AwayTeam']
        return f"recommendation: {RESOLUTION_MAP.get(winner, 'p3')}"
    elif game['Status'] == "Postponed":
        return "recommendation: p4"  # Market remains open
    elif game['Status'] == "Canceled":
        return "recommendation: p3"  # Resolve as 50-50
    return "recommendation: p4"  # Default case if status is unclear

if __name__ == "__main__":
    game_date = "2025-06-18"
    home_team = "Dodgers"
    away_team = "Padres"
    game = get_game_data(game_date, home_team, away_team)
    print(resolve_market(game))