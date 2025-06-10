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
DATE = "2025-05-30"
TEAM1 = "BOS"  # Boston Red Sox
TEAM2 = "ATL"  # Atlanta Braves
RESOLUTION_MAP = {
    TEAM1: "p2",  # Red Sox win
    TEAM2: "p1",  # Braves win
    "Postponed": "p4",  # Game postponed
    "Canceled": "p3",  # Game canceled
    "Scheduled": "p4",  # Game scheduled but not yet played
}

# API Configuration
API_ENDPOINT = "https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/"
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

def get_game_data(date):
    response = requests.get(f"{API_ENDPOINT}{date}", headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception("Failed to fetch data from API")

def analyze_game(games, team1, team2):
    for game in games:
        if game['HomeTeam'] == team1 and game['AwayTeam'] == team2:
            if game['Status'] == "Final":
                if game['HomeTeamRuns'] > game['AwayTeamRuns']:
                    return RESOLUTION_MAP[team1]
                else:
                    return RESOLUTION_MAP[team2]
            elif game['Status'] == "Postponed":
                return RESOLUTION_MAP["Postponed"]
            elif game['Status'] == "Canceled":
                return RESOLUTION_MAP["Canceled"]
            else:
                return RESOLUTION_MAP["Scheduled"]
    return "p4"  # No game found

def main():
    try:
        games = get_game_data(DATE)
        result = analyze_game(games, TEAM1, TEAM2)
        print(f"recommendation: {result}")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()