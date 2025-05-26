import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# Configuration for API requests
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/mlb/scores/json"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-proxy/mlb"

# Resolution map based on the game outcome
RESOLUTION_MAP = {
    "Rangers": "p1",
    "White Sox": "p2",
    "50-50": "p3"
}

def get_game_data(date, team1, team2):
    """ Fetch game data from the API """
    url = f"{PRIMARY_ENDPOINT}/GamesByDate/{date}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        games = response.json()
    except requests.RequestException:
        # Fallback to proxy endpoint
        url = f"{PROXY_ENDPOINT}/GamesByDate/{date}"
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        games = response.json()

    for game in games:
        if (game["HomeTeam"] == team1 and game["AwayTeam"] == team2) or \
           (game["HomeTeam"] == team2 and game["AwayTeam"] == team1):
            return game
    return None

def resolve_market(game):
    """ Determine the market resolution based on game data """
    if not game:
        return "recommendation: p3"  # No game found, resolve as 50-50
    if game["Status"] == "Final":
        home_runs = game["HomeTeamRuns"]
        away_runs = game["AwayTeamRuns"]
        if home_runs > away_runs:
            winner = game["HomeTeam"]
        else:
            winner = game["AwayTeam"]
        return f"recommendation: {RESOLUTION_MAP.get(winner, 'p3')}"
    elif game["Status"] in ["Canceled", "Postponed"]:
        return "recommendation: p3"  # Game not played or postponed
    else:
        return "recommendation: p3"  # Default to 50-50 if status is unclear

if __name__ == "__main__":
    # Define the game details
    game_date = "2025-05-23"
    team1 = "Texas Rangers"
    team2 = "Chicago White Sox"

    # Fetch game data and resolve the market
    game = get_game_data(game_date, team1, team2)
    result = resolve_market(game)
    print(result)