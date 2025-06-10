import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# Constants
DATE = "2025-05-28"
TEAM1 = "Tampa Bay Rays"
TEAM2 = "Minnesota Twins"
RESOLUTION_MAP = {
    TEAM1: "p2",  # Rays win
    TEAM2: "p1",  # Twins win
    "50-50": "p3",  # Game canceled or tie
    "Too early to resolve": "p4"  # Not enough data or game not completed
}

# Headers for API request
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

def get_games_by_date(date):
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{date}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to fetch data: {response.status_code} {response.text}")

def resolve_market(games):
    for game in games:
        if {game["HomeTeam"], game["AwayTeam"]} == {TEAM1, TEAM2}:
            if game["Status"] == "Final":
                home_team_runs = game["HomeTeamRuns"]
                away_team_runs = game["AwayTeamRuns"]
                if home_team_runs > away_team_runs:
                    return RESOLUTION_MAP[game["HomeTeam"]]
                else:
                    return RESOLUTION_MAP[game["AwayTeam"]]
            elif game["Status"] == "Canceled":
                return RESOLUTION_MAP["50-50"]
            elif game["Status"] == "Postponed":
                return RESOLUTION_MAP["Too early to resolve"]
    return RESOLUTION_MAP["Too early to resolve"]

if __name__ == "__main__":
    try:
        games = get_games_by_date(DATE)
        recommendation = resolve_market(games)
        print(f"recommendation: {recommendation}")
    except Exception as e:
        print(f"Error: {str(e)}")
        print("recommendation: p4")