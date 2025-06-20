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
DATE = "2025-06-11"
TEAM1 = "ATL"  # Atlanta Braves
TEAM2 = "MIL"  # Milwaukee Brewers
RESOLUTION_MAP = {
    TEAM1: "p2",  # Braves win
    TEAM2: "p1",  # Brewers win
    "Canceled": "p3",
    "Postponed": "p4",
    "In Progress": "p4"
}

# Headers for API request
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

def get_game_data(date):
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{date}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to fetch data: {response.status_code} {response.reason}")

def analyze_game_data(games):
    for game in games:
        if {game["HomeTeam"], game["AwayTeam"]} == {TEAM1, TEAM2}:
            if game["Status"] == "Final":
                if game["HomeTeamRuns"] > game["AwayTeamRuns"]:
                    return RESOLUTION_MAP[game["HomeTeam"]]
                else:
                    return RESOLUTION_MAP[game["AwayTeam"]]
            else:
                return RESOLUTION_MAP.get(game["Status"], "p4")
    return "p4"

if __name__ == "__main__":
    try:
        games = get_game_data(DATE)
        result = analyze_game_data(games)
        print(f"recommendation: {result}")
    except Exception as e:
        print(f"Error: {str(e)}")
        print("recommendation: p4")