import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# Configuration for headers and endpoints
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/mlb/scores/json"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-proxy/mlb"

# Resolution map based on the game outcome
RESOLUTION_MAP = {
    "Rockies": "p2",
    "Marlins": "p1",
    "50-50": "p3",
    "Too early to resolve": "p4"
}

def get_game_data(date, team1, team2):
    # Format the date for the API endpoint
    formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = f"{PRIMARY_ENDPOINT}/GamesByDate/{formatted_date}"
    proxy_url = f"{PROXY_ENDPOINT}/GamesByDate/{formatted_date}"

    # Try proxy endpoint first
    try:
        response = requests.get(proxy_url, headers=HEADERS, timeout=10)
        if not response.ok:
            raise Exception("Proxy failed")
        games = response.json()
    except Exception:
        # Fallback to primary endpoint
        response = requests.get(url, headers=HEADERS, timeout=10)
        if not response.ok:
            return None
        games = response.json()

    # Search for the specific game
    for game in games:
        if (game["HomeTeam"] == team1 and game["AwayTeam"] == team2) or \
           (game["HomeTeam"] == team2 and game["AwayTeam"] == team1):
            return game
    return None

def resolve_market(game):
    if not game:
        return RESOLUTION_MAP["Too early to resolve"]
    if game["Status"] == "Final":
        home_team_runs = game["HomeTeamRuns"]
        away_team_runs = game["AwayTeamRuns"]
        if home_team_runs > away_team_runs:
            winner = game["HomeTeam"]
        else:
            winner = game["AwayTeam"]
        return RESOLUTION_MAP.get(winner, "50-50")
    elif game["Status"] in ["Canceled", "Postponed"]:
        return RESOLUTION_MAP["50-50"]
    else:
        return RESOLUTION_MAP["Too early to resolve"]

if __name__ == "__main__":
    # Game details
    game_date = "2025-06-03"
    home_team = "Rockies"
    away_team = "Marlins"

    # Get game data and resolve the market
    game_info = get_game_data(game_date, home_team, away_team)
    recommendation = resolve_market(game_info)
    print(f"recommendation: {recommendation}")