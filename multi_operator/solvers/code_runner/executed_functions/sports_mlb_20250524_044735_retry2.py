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

# Game details
GAME_DATE = "2025-05-23"
TEAM1 = "PHI"  # Philadelphia Phillies
TEAM2 = "OAK"  # Oakland Athletics

# Resolution map
RESOLUTION_MAP = {
    TEAM1: "p2",  # Phillies win
    TEAM2: "p1",  # Athletics win
    "Postponed": "p4",  # Game postponed
    "Canceled": "p3",  # Game canceled
    "Unknown": "p4"  # Unknown or in-progress
}

def get_game_data(date):
    url = f"{PRIMARY_ENDPOINT}/GamesByDate/{date}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to fetch data: {response.status_code} {response.text}")

def resolve_game(games):
    for game in games:
        if {game["HomeTeam"], game["AwayTeam"]} == {TEAM1, TEAM2}:
            if game["Status"] == "Final":
                if game["HomeTeamRuns"] > game["AwayTeamRuns"]:
                    winner = game["HomeTeam"]
                else:
                    winner = game["AwayTeam"]
                return RESOLUTION_MAP.get(winner, "Unknown")
            else:
                return RESOLUTION_MAP.get(game["Status"], "Unknown")
    return "Unknown"

def main():
    try:
        games = get_game_data(GAME_DATE)
        result = resolve_game(games)
        print(f"recommendation: {RESOLUTION_MAP.get(result, 'Unknown')}")
    except Exception as e:
        print(f"Error: {str(e)}")
        print("recommendation: p4")  # Default to unresolved if there's an error

if __name__ == "__main__":
    main()