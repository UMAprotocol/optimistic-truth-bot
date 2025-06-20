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
DATE = "2025-06-18"
TEAM1 = "Texas Rangers"  # Corresponds to p1
TEAM2 = "Kansas City Royals"  # Corresponds to p2
RESOLUTION_MAP = {
    "Texas Rangers": "p1",
    "Kansas City Royals": "p2",
    "Postponed": "p4",
    "Canceled": "p3"
}

# Headers for API request
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

def get_game_data(date):
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{date}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to fetch data: {response.status_code} {response.text}")

def analyze_game_data(games, team1, team2):
    for game in games:
        if (game['HomeTeam'] == team1 and game['AwayTeam'] == team2) or (game['HomeTeam'] == team2 and game['AwayTeam'] == team1):
            if game['Status'] == "Final":
                if game['HomeTeamRuns'] > game['AwayTeamRuns']:
                    return RESOLUTION_MAP[game['HomeTeam']]
                elif game['HomeTeamRuns'] < game['AwayTeamRuns']:
                    return RESOLUTION_MAP[game['AwayTeam']]
            elif game['Status'] == "Postponed":
                return RESOLUTION_MAP["Postponed"]
            elif game['Status'] == "Canceled":
                return RESOLUTION_MAP["Canceled"]
    return "p4"  # If no relevant game is found or it's still in progress

def main():
    try:
        games = get_game_data(DATE)
        result = analyze_game_data(games, TEAM1, TEAM2)
        print(f"recommendation: {result}")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()