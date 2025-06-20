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
DATE = "2025-06-16"
TEAM1 = "IND"  # Indiana Pacers
TEAM2 = "OKC"  # Oklahoma City Thunder
RESOLUTION_MAP = {
    TEAM1: "p2",  # Pacers win
    TEAM2: "p1",  # Thunder win
    "50-50": "p3",
    "Too early to resolve": "p4",
}

# Function to get game data
def get_game_data(date):
    url = f"https://api.sportsdata.io/v3/nba/scores/json/GamesByDate/{date}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to fetch data: {response.status_code} {response.text}")

# Determine the outcome
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
                return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]
            elif game["Status"] == "Canceled":
                return "recommendation: " + RESOLUTION_MAP["50-50"]
    return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

# Main execution
if __name__ == "__main__":
    try:
        games = get_game_data(DATE)
        result = determine_outcome(games, TEAM1, TEAM2)
        print(result)
    except Exception as e:
        print(f"Error: {str(e)}")