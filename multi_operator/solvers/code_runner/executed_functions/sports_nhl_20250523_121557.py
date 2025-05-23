import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NHL_API_KEY")

# Constants
DATE = "2025-05-22"
TEAM1 = "FLA"  # Florida Panthers
TEAM2 = "CAR"  # Carolina Hurricanes
RESOLUTION_MAP = {
    TEAM1: "p2",  # Panthers win
    TEAM2: "p1",  # Hurricanes win
    "50-50": "p3",
    "Too early to resolve": "p4",
}

# Headers for API request
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

# Function to get game data
def get_game_data(date):
    url = f"https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/{date}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    else:
        response.raise_for_status()

# Function to determine the outcome
def determine_outcome(games, team1, team2):
    for game in games:
        if {game["HomeTeam"], game["AwayTeam"]} == {team1, team2}:
            if game["Status"] == "Final":
                if game["HomeTeam"] == team1 and game["HomeTeamScore"] > game["AwayTeamScore"]:
                    return RESOLUTION_MAP[team1]
                elif game["AwayTeam"] == team1 and game["AwayTeamScore"] > game["HomeTeamScore"]:
                    return RESOLUTION_MAP[team1]
                elif game["HomeTeam"] == team2 and game["HomeTeamScore"] > game["AwayTeamScore"]:
                    return RESOLUTION_MAP[team2]
                elif game["AwayTeam"] == team2 and game["AwayTeamScore"] > game["HomeTeamScore"]:
                    return RESOLUTION_MAP[team2]
            elif game["Status"] == "Postponed":
                return RESOLUTION_MAP["Too early to resolve"]
            elif game["Status"] == "Canceled":
                return RESOLUTION_MAP["50-50"]
    return RESOLUTION_MAP["Too early to resolve"]

# Main execution
if __name__ == "__main__":
    try:
        games = get_game_data(DATE)
        result = determine_outcome(games, TEAM1, TEAM2)
        print("recommendation:", result)
    except Exception as e:
        print("Error:", str(e))