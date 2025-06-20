import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# Headers for API requests
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

# Game details
GAME_DATE = "2025-06-19"
TEAM1 = "Baltimore Orioles"
TEAM2 = "Tampa Bay Rays"

# Resolution map based on the game outcome
RESOLUTION_MAP = {
    TEAM1: "p2",  # Orioles win
    TEAM2: "p1",  # Rays win
    "Postponed": "p4",  # Game postponed
    "Canceled": "p3",  # Game canceled
    "Unknown": "p4"  # Unknown or in-progress
}

# Function to get game data from SportsDataIO
def get_game_data(date):
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{date}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    else:
        return None

# Function to determine the outcome of the game
def determine_outcome(games, team1, team2):
    for game in games:
        if (game['HomeTeam'] == team1 and game['AwayTeam'] == team2) or (game['HomeTeam'] == team2 and game['AwayTeam'] == team1):
            if game['Status'] == "Final":
                if game['HomeTeamRuns'] > game['AwayTeamRuns']:
                    return RESOLUTION_MAP[game['HomeTeam']]
                elif game['AwayTeamRuns'] > game['HomeTeamRuns']:
                    return RESOLUTION_MAP[game['AwayTeam']]
            elif game['Status'] == "Postponed":
                return RESOLUTION_MAP["Postponed"]
            elif game['Status'] == "Canceled":
                return RESOLUTION_MAP["Canceled"]
    return RESOLUTION_MAP["Unknown"]

# Main function to run the program
def main():
    games = get_game_data(GAME_DATE)
    if games:
        result = determine_outcome(games, TEAM1, TEAM2)
        print(f"recommendation: {result}")
    else:
        print("recommendation: p4")  # Unable to retrieve data

if __name__ == "__main__":
    main()