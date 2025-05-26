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
DATE = "2025-05-24"
TEAM1 = "Seattle Mariners"
TEAM2 = "Houston Astros"
RESOLUTION_MAP = {
    TEAM1: "p2",  # Mariners win
    TEAM2: "p1",  # Astros win
    "Postponed": "p4",  # Game postponed
    "Canceled": "p3",  # Game canceled
    "Unknown": "p4"  # Unknown or in-progress
}

# Headers for API request
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

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
        if game['HomeTeam'] == team1 and game['AwayTeam'] == team2 or \
           game['HomeTeam'] == team2 and game['AwayTeam'] == team1:
            if game['Status'] == "Final":
                if game['HomeTeamRuns'] > game['AwayTeamRuns']:
                    return RESOLUTION_MAP[game['HomeTeam']]
                else:
                    return RESOLUTION_MAP[game['AwayTeam']]
            elif game['Status'] == "Postponed":
                return RESOLUTION_MAP["Postponed"]
            elif game['Status'] == "Canceled":
                return RESOLUTION_MAP["Canceled"]
            else:
                return RESOLUTION_MAP["Unknown"]
    return RESOLUTION_MAP["Unknown"]

# Main execution block
if __name__ == "__main__":
    try:
        games = get_game_data(DATE)
        result = determine_outcome(games, TEAM1, TEAM2)
        print(f"recommendation: {result}")
    except Exception as e:
        print(f"Error: {str(e)}")
        print("recommendation: p4")  # Fallback in case of any error