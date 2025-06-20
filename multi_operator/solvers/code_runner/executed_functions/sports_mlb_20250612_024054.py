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
GAME_DATE = "2025-06-11"
HOME_TEAM = "Royals"
AWAY_TEAM = "Yankees"

# Resolution map
RESOLUTION_MAP = {
    "Royals": "p1",
    "Yankees": "p2",
    "50-50": "p3",
    "Too early to resolve": "p4"
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
def determine_outcome(games, home_team, away_team):
    for game in games:
        if game['HomeTeam'] == home_team and game['AwayTeam'] == away_team:
            if game['Status'] == "Final":
                home_score = game['HomeTeamRuns']
                away_score = game['AwayTeamRuns']
                if home_score > away_score:
                    return RESOLUTION_MAP[home_team]
                elif away_score > home_score:
                    return RESOLUTION_MAP[away_team]
            elif game['Status'] == "Canceled":
                return RESOLUTION_MAP["50-50"]
            elif game['Status'] == "Postponed":
                return RESOLUTION_MAP["Too early to resolve"]
    return RESOLUTION_MAP["Too early to resolve"]

# Main function to run the program
def main():
    games = get_game_data(GAME_DATE)
    if games:
        result = determine_outcome(games, HOME_TEAM, AWAY_TEAM)
        print(f"recommendation: {result}")
    else:
        print("recommendation: p4")  # Unable to retrieve data

if __name__ == "__main__":
    main()