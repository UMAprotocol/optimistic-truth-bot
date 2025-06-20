import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

# Constants
DATE = "2025-06-13"
TEAM1 = "New York Mets"
TEAM2 = "Tampa Bay Rays"
RESOLUTION_MAP = {
    TEAM1: "p1",
    TEAM2: "p2",
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

def resolve_market(game):
    if not game:
        return RESOLUTION_MAP["Too early to resolve"]
    if game["Status"] == "Final":
        if game["HomeTeamRuns"] > game["AwayTeamRuns"]:
            winner = game["HomeTeam"]
        else:
            winner = game["AwayTeam"]
        return RESOLUTION_MAP[winner]
    elif game["Status"] in ["Canceled", "Postponed"]:
        return RESOLUTION_MAP["50-50"]
    else:
        return RESOLUTION_MAP["Too early to resolve"]

# Main execution
def main():
    # Fetch games by date
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{DATE}"
    games = get_json_response(url)
    if games is None:
        print("Failed to fetch games data.")
        return

    # Find the specific game
    game = find_game(games, TEAM1, TEAM2)
    if not game:
        print("Game not found.")
        return

    # Resolve the market based on the game status and outcome
    recommendation = resolve_market(game)
    print(f"recommendation: {recommendation}")

if __name__ == "__main__":
    main()