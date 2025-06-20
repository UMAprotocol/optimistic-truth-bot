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
TEAM1 = "Toronto Blue Jays"  # p1
TEAM2 = "Arizona Diamondbacks"  # p2

# Resolution map
RESOLUTION_MAP = {
    "Blue Jays": "p1",
    "Diamondbacks": "p2",
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

def find_game(date, team1, team2):
    formatted_date = datetime.strptime(date, "%Y-%m-%d").date()
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{formatted_date}"
    games = get_json_response(url)
    if games:
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
if __name__ == "__main__":
    game_info = find_game(DATE, TEAM1, TEAM2)
    recommendation = resolve_market(game_info)
    print(f"recommendation: {recommendation}")