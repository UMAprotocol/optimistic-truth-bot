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
GAME_DATE = "2025-05-28"
TEAM1 = "TOR"  # Toronto Blue Jays
TEAM2 = "TEX"  # Texas Rangers
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

# Resolution map based on the game outcome
RESOLUTION_MAP = {
    "Blue Jays": "p2",
    "Rangers": "p1",
    "50-50": "p3",
    "Too early to resolve": "p4"
}

def get_game_data(date):
    """ Fetch game data for a specific date """
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{date}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    else:
        return None

def analyze_game_data(games):
    """ Analyze game data to determine the outcome """
    for game in games:
        if game['HomeTeam'] == TEAM2 and game['AwayTeam'] == TEAM1:
            if game['Status'] == "Final":
                home_score = game['HomeTeamRuns']
                away_score = game['AwayTeamRuns']
                if home_score > away_score:
                    return RESOLUTION_MAP["Rangers"]
                elif away_score > home_score:
                    return RESOLUTION_MAP["Blue Jays"]
            elif game['Status'] == "Canceled":
                return RESOLUTION_MAP["50-50"]
            elif game['Status'] == "Postponed":
                return RESOLUTION_MAP["Too early to resolve"]
    return RESOLUTION_MAP["Too early to resolve"]

def main():
    games = get_game_data(GAME_DATE)
    if games:
        result = analyze_game_data(games)
    else:
        result = RESOLUTION_MAP["Too early to resolve"]
    print("recommendation:", result)

if __name__ == "__main__":
    main()