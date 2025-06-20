import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# API headers
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

# Constants
DATE = "2025-06-19"
TEAM1 = "Minnesota Twins"
TEAM2 = "Cincinnati Reds"
RESOLUTION_MAP = {
    "Twins": "p2",
    "Reds": "p1",
    "50-50": "p3",
    "Too early to resolve": "p4"
}

# Helper functions
def get_json_response(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

def find_game(games, team1, team2):
    for game in games:
        if {game["HomeTeam"], game["AwayTeam"]} == {team1, team2}:
            return game
    return None

def resolve_game_status(game):
    if game["Status"] == "Final":
        home_runs = game["HomeTeamRuns"]
        away_runs = game["AwayTeamRuns"]
        if home_runs > away_runs:
            winner = game["HomeTeam"]
        else:
            winner = game["AwayTeam"]
        return RESOLUTION_MAP[winner]
    elif game["Status"] == "Postponed":
        return RESOLUTION_MAP["Too early to resolve"]
    elif game["Status"] == "Canceled":
        return RESOLUTION_MAP["50-50"]
    else:
        return RESOLUTION_MAP["Too early to resolve"]

# Main execution
def main():
    # Construct URL for the game date
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{DATE}"
    games = get_json_response(url)
    
    if not games:
        print("recommendation:", RESOLUTION_MAP["Too early to resolve"])
        return

    # Find the specific game
    game = find_game(games, TEAM1, TEAM2)
    if not game:
        print("recommendation:", RESOLUTION_MAP["Too early to resolve"])
        return

    # Resolve based on game status
    recommendation = resolve_game_status(game)
    print("recommendation:", recommendation)

if __name__ == "__main__":
    main()