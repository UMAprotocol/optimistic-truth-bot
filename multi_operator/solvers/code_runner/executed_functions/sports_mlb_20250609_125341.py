import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# API headers
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

# Game details
GAME_DATE = "2025-05-28"
TEAM1 = "SF"  # San Francisco Giants
TEAM2 = "DET"  # Detroit Tigers

# Resolution map
RESOLUTION_MAP = {
    TEAM1: "p2",  # Giants win
    TEAM2: "p1",  # Tigers win
    "Postponed": "p4",  # Game postponed
    "Canceled": "p3",  # Game canceled
    "Scheduled": "p4"  # Game scheduled but not yet played
}

# Function to get game data
def get_game_data(date):
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{date}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        games = response.json()
        for game in games:
            if game['HomeTeam'] == TEAM2 and game['AwayTeam'] == TEAM1:
                return game
            elif game['HomeTeam'] == TEAM1 and game['AwayTeam'] == TEAM2:
                return game
    return None

# Function to determine the outcome
def determine_outcome(game):
    if not game:
        return "p4"  # No game data found
    if game['Status'] == "Final":
        if game['HomeTeamRuns'] > game['AwayTeamRuns']:
            return RESOLUTION_MAP[game['HomeTeam']]
        elif game['AwayTeamRuns'] > game['HomeTeamRuns']:
            return RESOLUTION_MAP[game['AwayTeam']]
    elif game['Status'] in ["Postponed", "Canceled"]:
        return RESOLUTION_MAP[game['Status']]
    return RESOLUTION_MAP["Scheduled"]

# Main execution
if __name__ == "__main__":
    game_info = get_game_data(GAME_DATE)
    result = determine_outcome(game_info)
    print(f"recommendation: {result}")