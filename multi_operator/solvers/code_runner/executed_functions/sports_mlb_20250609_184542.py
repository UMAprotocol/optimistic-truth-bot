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
GAME_DATE = "2025-05-31"
TEAM1 = "Pirates"
TEAM2 = "Padres"

# Resolution map
RESOLUTION_MAP = {
    "Pirates": "p2",  # Pittsburgh Pirates win
    "Padres": "p1",   # San Diego Padres win
    "50-50": "p3",    # Game canceled or tie
    "Too early to resolve": "p4"  # Not enough data or game not played yet
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
        if game['AwayTeam'] == team1 and game['HomeTeam'] == team2 or \
           game['AwayTeam'] == team2 and game['HomeTeam'] == team1:
            if game['Status'] == "Final":
                if game['AwayTeamRuns'] > game['HomeTeamRuns']:
                    return RESOLUTION_MAP[game['AwayTeam']]
                elif game['HomeTeamRuns'] > game['AwayTeamRuns']:
                    return RESOLUTION_MAP[game['HomeTeam']]
            elif game['Status'] == "Canceled":
                return RESOLUTION_MAP["50-50"]
            elif game['Status'] == "Postponed":
                return RESOLUTION_MAP["Too early to resolve"]
    return RESOLUTION_MAP["Too early to resolve"]

# Main function to run the program
def main():
    today = datetime.now().strftime("%Y-%m-%d")
    if today > GAME_DATE:
        games = get_game_data(GAME_DATE)
        if games:
            result = determine_outcome(games, TEAM1, TEAM2)
        else:
            result = RESOLUTION_MAP["Too early to resolve"]
    else:
        result = RESOLUTION_MAP["Too early to resolve"]
    print("recommendation:", result)

if __name__ == "__main__":
    main()