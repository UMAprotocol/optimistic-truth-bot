import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

# Constants
DATE = "2025-05-26"
TEAM1 = "Los Angeles Dodgers"
TEAM2 = "Cleveland Guardians"
RESOLUTION_MAP = {
    TEAM1: "p2",  # Dodgers win
    TEAM2: "p1",  # Guardians win
    "50-50": "p3",  # Game canceled
    "Too early to resolve": "p4"  # Not enough data or game postponed
}

# Function to get game data
def get_game_data(date):
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{date}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    else:
        return None

# Function to determine the outcome
def determine_outcome(games, team1, team2):
    for game in games:
        if game['HomeTeam'] == team1 and game['AwayTeam'] == team2 or \
           game['HomeTeam'] == team2 and game['AwayTeam'] == team1:
            if game['Status'] == "Final":
                if game['HomeTeamRuns'] > game['AwayTeamRuns']:
                    return RESOLUTION_MAP[game['HomeTeam']]
                elif game['AwayTeamRuns'] > game['HomeTeamRuns']:
                    return RESOLUTION_MAP[game['AwayTeam']]
            elif game['Status'] == "Canceled":
                return RESOLUTION_MAP["50-50"]
            elif game['Status'] == "Postponed":
                return RESOLUTION_MAP["Too early to resolve"]
    return RESOLUTION_MAP["Too early to resolve"]

# Main execution
if __name__ == "__main__":
    games = get_game_data(DATE)
    if games:
        result = determine_outcome(games, TEAM1, TEAM2)
    else:
        result = RESOLUTION_MAP["Too early to resolve"]
    print("recommendation:", result)