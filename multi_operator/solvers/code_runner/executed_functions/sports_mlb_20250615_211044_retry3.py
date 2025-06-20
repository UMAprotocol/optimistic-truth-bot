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
DATE = "2025-06-15"
TEAM1 = "Athletics"  # Corresponds to p2
TEAM2 = "Royals"     # Corresponds to p1
RESOLUTION_MAP = {
    "Athletics": "p2",
    "Royals": "p1",
    "Canceled": "p3",
    "Postponed": "p4",
    "In Progress": "p4"
}

# Headers for API request
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

# Function to get game data
def get_game_data(date, team1, team2):
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{date}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        raise Exception("Failed to fetch data from API")
    games = response.json()
    for game in games:
        if (game["HomeTeam"] == team1 and game["AwayTeam"] == team2) or \
           (game["HomeTeam"] == team2 and game["AwayTeam"] == team1):
            return game
    return None

# Function to determine the outcome
def determine_outcome(game):
    if not game:
        return "p4"  # Game not found, assume in progress or error
    if game["Status"] == "Final":
        if game["HomeTeamRuns"] > game["AwayTeamRuns"]:
            return RESOLUTION_MAP[game["HomeTeam"]]
        elif game["HomeTeamRuns"] < game["AwayTeamRuns"]:
            return RESOLUTION_MAP[game["AwayTeam"]]
    elif game["Status"] == "Canceled":
        return "p3"
    elif game["Status"] == "Postponed":
        return "p4"
    return "p4"

# Main execution
if __name__ == "__main__":
    game_info = get_game_data(DATE, TEAM1, TEAM2)
    result = determine_outcome(game_info)
    print(f"recommendation: {result}")