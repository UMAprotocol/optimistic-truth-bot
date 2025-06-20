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
GAME_DATE = "2025-06-11"
HOME_TEAM = "Cardinals"
AWAY_TEAM = "Blue Jays"

# Resolution map based on the game outcome
RESOLUTION_MAP = {
    "Cardinals": "p1",  # Home team wins
    "Blue Jays": "p2",  # Away team wins
    "50-50": "p3",      # Game canceled or postponed without resolution
    "Too early to resolve": "p4"  # Not enough data or game not completed
}

# Function to get game data from the API
def get_game_data(date):
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{date}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    else:
        return None

# Function to determine the outcome of the game
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
    else:
        result = RESOLUTION_MAP["Too early to resolve"]
    print("recommendation:", result)

if __name__ == "__main__":
    main()