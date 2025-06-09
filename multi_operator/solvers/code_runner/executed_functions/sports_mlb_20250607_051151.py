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
DATE = "2025-06-06"
TEAM1 = "ATL"  # Atlanta Braves
TEAM2 = "SF"   # San Francisco Giants
RESOLUTION_MAP = {
    TEAM1: "p2",  # Braves win
    TEAM2: "p1",  # Giants win
    "Postponed": "p4",  # Game postponed
    "Canceled": "p3",   # Game canceled
    "Unknown": "p4"     # Unknown or in-progress
}

# API Configuration
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
BASE_URL = "https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/"

def get_game_data(date):
    url = f"{BASE_URL}{date}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        games = response.json()
        return games
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

def analyze_game(games, team1, team2):
    for game in games:
        if {game["HomeTeam"], game["AwayTeam"]} == {team1, team2}:
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
    games = get_game_data(DATE)
    if games:
        result = analyze_game(games, TEAM1, TEAM2)
        print(f"recommendation: {RESOLUTION_MAP.get(result, 'Unknown')}")
    else:
        print("recommendation: p4")  # Unable to retrieve data

if __name__ == "__main__":
    main()