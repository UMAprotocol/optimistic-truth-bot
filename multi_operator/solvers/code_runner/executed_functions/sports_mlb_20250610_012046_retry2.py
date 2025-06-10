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
DATE = "2025-06-01"
TEAM1 = "Los Angeles Angels"
TEAM2 = "Cleveland Guardians"
RESOLUTION_MAP = {
    TEAM1: "p2",  # Angels win
    TEAM2: "p1",  # Guardians win
    "50-50": "p3",  # Game canceled or tie
    "Too early to resolve": "p4"  # Not enough data or game not completed
}

# Headers for API request
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

# Function to get game data
def get_game_data(date):
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{date}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to fetch data: {response.status_code} {response.text}")

# Function to determine the outcome
def determine_outcome(games, team1, team2):
    for game in games:
        if {game["HomeTeam"], game["AwayTeam"]} == {team1, team2}:
            if game["Status"] == "Final":
                if game["HomeTeamRuns"] > game["AwayTeamRuns"]:
                    winner = game["HomeTeam"]
                else:
                    winner = game["AwayTeam"]
                return RESOLUTION_MAP.get(winner, "p4")
            elif game["Status"] in ["Canceled", "Postponed"]:
                return "p3"
            else:
                return "p4"
    return "p4"

# Main execution
if __name__ == "__main__":
    try:
        games = get_game_data(DATE)
        result = determine_outcome(games, TEAM1, TEAM2)
        print(f"recommendation: {result}")
    except Exception as e:
        print(f"Error: {str(e)}")
        print("recommendation: p4")