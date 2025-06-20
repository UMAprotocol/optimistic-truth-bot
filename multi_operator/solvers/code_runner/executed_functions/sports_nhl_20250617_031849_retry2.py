import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NBA_API_KEY")

# Constants
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
GAME_DATE = "2025-06-16"
TEAM1 = "IND"  # Indiana Pacers
TEAM2 = "OKC"  # Oklahoma City Thunder
RESOLUTION_MAP = {
    TEAM1: "p2",  # Pacers win
    TEAM2: "p1",  # Thunder win
    "Postponed": "p4",  # Game postponed
    "Canceled": "p3",  # Game canceled
    "Unknown": "p4"  # Unknown or in-progress
}

# Function to get game data
def get_game_data(date):
    url = f"https://api.sportsdata.io/v3/nba/scores/json/GamesByDate/{date}"
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
                if game["HomeTeam"] == team1 and game["HomeTeamScore"] > game["AwayTeamScore"]:
                    return RESOLUTION_MAP[team1]
                elif game["AwayTeam"] == team1 and game["AwayTeamScore"] > game["HomeTeamScore"]:
                    return RESOLUTION_MAP[team1]
                else:
                    return RESOLUTION_MAP[team2]
            elif game["Status"] == "Postponed":
                return RESOLUTION_MAP["Postponed"]
            elif game["Status"] == "Canceled":
                return RESOLUTION_MAP["Canceled"]
    return RESOLUTION_MAP["Unknown"]

# Main execution
if __name__ == "__main__":
    try:
        games = get_game_data(GAME_DATE)
        result = determine_outcome(games, TEAM1, TEAM2)
        print(f"recommendation: {result}")
    except Exception as e:
        print(f"Error: {str(e)}")
        print("recommendation: p4")  # Fallback in case of any error