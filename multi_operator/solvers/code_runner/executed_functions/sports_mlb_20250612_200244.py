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
GAME_DATE = "2025-06-12"
TEAM1 = "Texas Rangers"
TEAM2 = "Minnesota Twins"

# Resolution map
RESOLUTION_MAP = {
    "Rangers": "p2",  # Texas Rangers win
    "Twins": "p1",    # Minnesota Twins win
    "50-50": "p3",    # Game canceled or tie
    "Too early to resolve": "p4"  # Not enough data or game not completed
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
    # Construct URL for the game date
    url = f"{PRIMARY_ENDPOINT}/GamesByDate/{GAME_DATE}"
    games = get_data(url, HEADERS)
    if not games:
        # Try proxy if primary fails
        games = get_data(PROXY_ENDPOINT, HEADERS)
        if not games:
            return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

    # Find the specific game
    game = find_game(games, TEAM1, TEAM2)
    # Resolve the market based on the game data
    result = resolve_market(game)
    print("recommendation:", result)

if __name__ == "__main__":
    main()