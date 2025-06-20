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
DATE = "2025-06-10"
TEAM1 = "Boston Red Sox"
TEAM2 = "Tampa Bay Rays"
RESOLUTION_MAP = {
    TEAM1: "p1",
    TEAM2: "p2",
    "Postponed": "p4",
    "Canceled": "p3",
    "50-50": "p3"
}

# Function to get data from API
def get_data(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

# Function to find the game and determine the outcome
def find_game_and_outcome():
    date_formatted = datetime.strptime(DATE, "%Y-%m-%d").date()
    games_url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{date_formatted}"
    games_data = get_data(games_url)

    if games_data:
        for game in games_data:
            if {game["HomeTeam"], game["AwayTeam"]} == {TEAM1, TEAM2}:
                if game["Status"] == "Final":
                    if game["HomeTeamRuns"] > game["AwayTeamRuns"]:
                        winner = game["HomeTeam"]
                    else:
                        winner = game["AwayTeam"]
                    return RESOLUTION_MAP.get(winner, "p4")
                elif game["Status"] == "Postponed":
                    return RESOLUTION_MAP["Postponed"]
                elif game["Status"] == "Canceled":
                    return RESOLUTION_MAP["Canceled"]
    return "p4"

# Main execution
if __name__ == "__main__":
    recommendation = find_game_and_outcome()
    print(f"recommendation: {recommendation}")