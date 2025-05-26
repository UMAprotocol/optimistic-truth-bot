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
DATE = "2025-05-24"
TEAM1 = "Delhi Capitals"  # p2
TEAM2 = "Punjab Kings"    # p1
RESOLUTION_MAP = {
    "DEL": "p2",  # Delhi Capitals
    "PUN": "p1",  # Punjab Kings
    "50-50": "p3",
    "Too early to resolve": "p4",
}

# API Configuration
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/"

# Function to get games data
def get_games_by_date(date):
    url = f"{PRIMARY_ENDPOINT}{date}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"API request failed with status {response.status_code}: {response.text}")

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

# Main execution block
if __name__ == "__main__":
    try:
        games = get_games_by_date(DATE)
        recommendation = determine_outcome(games, "DEL", "PUN")
        print("recommendation:", recommendation)
    except Exception as e:
        print(f"Error: {str(e)}")