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
    "Reds": "p2",
    "Cubs": "p1",
    "50-50": "p3",
    "Too early to resolve": "p4"
}

# Helper functions
def get_data(url, proxy=False):
    endpoint = PROXY_ENDPOINT if proxy else PRIMARY_ENDPOINT
    try:
        response = requests.get(f"{endpoint}{url}", headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if proxy:
            print("Proxy failed, trying primary endpoint.")
            return get_data(url, proxy=False)
        else:
            print(f"Failed to retrieve data: {e}")
            return None

def find_game(date, team1, team2):
    games = get_data(f"/GamesByDate/{date}")
    if games:
        for game in games:
            if (game['HomeTeam'] == team1 and game['AwayTeam'] == team2) or \
               (game['HomeTeam'] == team2 and game['AwayTeam'] == team1):
                return game
    return None

def resolve_market(game):
    if not game:
        return RESOLUTION_MAP["Too early to resolve"]
    if game['Status'] == 'Final':
        if game['HomeTeamRuns'] > game['AwayTeamRuns']:
            winner = game['HomeTeam']
        else:
            winner = game['AwayTeam']
        return RESOLUTION_MAP.get(winner, "50-50")
    elif game['Status'] in ['Canceled', 'Postponed']:
        return RESOLUTION_MAP["50-50"]
    else:
        return RESOLUTION_MAP["Too early to resolve"]

# Main execution
if __name__ == "__main__":
    game_date = "2025-06-01"
    team1 = "CIN"  # Cincinnati Reds
    team2 = "CHC"  # Chicago Cubs

    game = find_game(game_date, team1, team2)
    recommendation = resolve_market(game)
    print(f"recommendation: {recommendation}")