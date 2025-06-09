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
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
DATE = "2025-06-07"
TEAM1 = "DET"  # Detroit Tigers
TEAM2 = "CHC"  # Chicago Cubs
RESOLUTION_MAP = {
    TEAM1: "p1",
    TEAM2: "p2",
    "Postponed": "p4",
    "Canceled": "p3",
    "Final": "final"
}

# Function to get game data
def get_game_data(date):
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{date}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception("Failed to fetch game data")

# Function to determine the outcome
def determine_outcome(games, team1, team2):
    for game in games:
        if game['HomeTeam'] == team1 and game['AwayTeam'] == team2:
            status = game['Status']
            if status == "Final":
                home_score = game['HomeTeamRuns']
                away_score = game['AwayTeamRuns']
                if home_score > away_score:
                    return RESOLUTION_MAP[team1]
                else:
                    return RESOLUTION_MAP[team2]
            else:
                return RESOLUTION_MAP.get(status, "p4")
    return "p4"

# Main execution
if __name__ == "__main__":
    try:
        games = get_game_data(DATE)
        recommendation = determine_outcome(games, TEAM1, TEAM2)
        print(f"recommendation: {recommendation}")
    except Exception as e:
        print(f"Error: {str(e)}")