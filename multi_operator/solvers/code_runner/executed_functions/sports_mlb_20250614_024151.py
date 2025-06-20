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
GAME_DATE = "2025-06-13"
HOME_TEAM = "Texas Rangers"
AWAY_TEAM = "Chicago White Sox"

# Resolution map
RESOLUTION_MAP = {
    HOME_TEAM: "p1",  # Rangers win
    AWAY_TEAM: "p2",  # White Sox win
    "50-50": "p3",    # Game canceled or tie
    "Too early to resolve": "p4"  # Not enough data or game not completed
}

# Function to get game data
def get_game_data(date):
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{date}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        games = response.json()
        for game in games:
            if game['HomeTeam'] == HOME_TEAM and game['AwayTeam'] == AWAY_TEAM:
                return game
    return None

# Function to determine the outcome
def determine_outcome(game):
    if not game:
        return RESOLUTION_MAP["Too early to resolve"]
    if game['Status'] == "Final":
        if game['HomeTeamRuns'] > game['AwayTeamRuns']:
            return RESOLUTION_MAP[HOME_TEAM]
        elif game['HomeTeamRuns'] < game['AwayTeamRuns']:
            return RESOLUTION_MAP[AWAY_TEAM]
    elif game['Status'] == "Canceled":
        return RESOLUTION_MAP["50-50"]
    elif game['Status'] == "Postponed":
        return RESOLUTION_MAP["Too early to resolve"]
    return RESOLUTION_MAP["Too early to resolve"]

# Main execution
if __name__ == "__main__":
    game_info = get_game_data(GAME_DATE)
    result = determine_outcome(game_info)
    print("recommendation:", result)