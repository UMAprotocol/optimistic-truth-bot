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
DATE = "2025-06-17"
TEAM1 = "Houston Astros"
TEAM2 = "Oakland Athletics"
RESOLUTION_MAP = {
    "Astros": "p2",
    "Athletics": "p1",
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
    date_formatted = datetime.strptime(DATE, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{date_formatted}"
    games = get_json_response(url)

    if games is None:
        print("recommendation:", RESOLUTION_MAP["Too early to resolve"])
        return

    # Find the specific game
    game = find_game(games, TEAM1, TEAM2)
    # Resolve the game status
    recommendation = resolve_game_status(game)
    print("recommendation:", recommendation)

if __name__ == "__main__":
    main()