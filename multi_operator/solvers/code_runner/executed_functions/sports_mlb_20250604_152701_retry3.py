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
TEAM1 = "Washington Nationals"
TEAM2 = "Arizona Diamondbacks"
RESOLUTION_MAP = {
    TEAM1: "p2",  # Nationals win
    TEAM2: "p1",  # Diamondbacks win
    "Postponed": "p4",  # Game postponed
    "Canceled": "p3",  # Game canceled
    "Unknown": "p4"  # Unknown or in-progress
}

# Headers for API request
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

def get_game_data(date):
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{date}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to fetch data: {response.status_code} {response.reason}")

def resolve_market(games, team1, team2):
    for game in games:
        if (game['HomeTeam'] == team1 or game['AwayTeam'] == team1) and \
           (game['HomeTeam'] == team2 or game['AwayTeam'] == team2):
            if game['Status'] == "Final":
                if game['HomeTeamRuns'] > game['AwayTeamRuns']:
                    winner = game['HomeTeam']
                else:
                    winner = game['AwayTeam']
                return RESOLUTION_MAP.get(winner, "Unknown")
            else:
                return RESOLUTION_MAP.get(game['Status'], "Unknown")
    return "Unknown"

def main():
    try:
        games = get_game_data(DATE)
        recommendation = resolve_market(games, TEAM1, TEAM2)
        print(f"recommendation: {recommendation}")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()