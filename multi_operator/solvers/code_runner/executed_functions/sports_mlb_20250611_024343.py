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
GAME_DATE = "2025-06-10"
TEAM1 = "New York Yankees"
TEAM2 = "Kansas City Royals"
RESOLUTION_MAP = {
    TEAM1: "p2",  # Yankees win
    TEAM2: "p1",  # Royals win
    "Postponed": "p4",  # Game postponed
    "Canceled": "p3",  # Game canceled
    "Unknown": "p4"  # Unknown or in-progress
}

# Function to get game data
def get_game_data(date):
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{date}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to fetch data: {response.status_code} {response.reason}")

# Function to determine the outcome
def determine_outcome(games, team1, team2):
    for game in games:
        if (game['HomeTeam'] == team1 or game['AwayTeam'] == team1) and (game['HomeTeam'] == team2 or game['AwayTeam'] == team2):
            if game['Status'] == "Final":
                if game['HomeTeamRuns'] > game['AwayTeamRuns']:
                    winner = game['HomeTeam']
                else:
                    winner = game['AwayTeam']
                return RESOLUTION_MAP.get(winner, "Unknown")
            elif game['Status'] == "Postponed":
                return RESOLUTION_MAP["Postponed"]
            elif game['Status'] == "Canceled":
                return RESOLUTION_MAP["Canceled"]
    return "Unknown"

# Main execution
if __name__ == "__main__":
    try:
        games = get_game_data(GAME_DATE)
        result = determine_outcome(games, TEAM1, TEAM2)
        print(f"recommendation: {RESOLUTION_MAP.get(result, 'Unknown')}")
    except Exception as e:
        print(f"Error: {str(e)}")
        print("recommendation: p4")  # Default to unresolved if there's an error