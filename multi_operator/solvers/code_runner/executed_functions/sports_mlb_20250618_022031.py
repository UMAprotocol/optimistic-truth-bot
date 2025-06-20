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

# Constants for the game
GAME_DATE = "2025-06-17"
HOME_TEAM = "White Sox"
AWAY_TEAM = "Cardinals"

# Resolution map based on the game outcome
RESOLUTION_MAP = {
    "White Sox": "p1",  # Home team wins
    "Cardinals": "p2",  # Away team wins
    "50-50": "p3",      # Game canceled or postponed without resolution
    "Too early to resolve": "p4"  # Not enough data or game not completed
}

# Function to fetch game data
def fetch_game_data(date):
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
                # Check if the game is rescheduled within the season
                rescheduled_game = fetch_game_data(datetime.strptime(date, "%Y-%m-%d").strftime("%Y"))
                if rescheduled_game:
                    return determine_outcome(rescheduled_game, home_team, away_team)
                else:
                    return RESOLUTION_MAP["50-50"]
    return RESOLUTION_MAP["Too early to resolve"]

# Main function to run the program
if __name__ == "__main__":
    games = fetch_game_data(GAME_DATE)
    if games:
        recommendation = determine_outcome(games, HOME_TEAM, AWAY_TEAM)
    else:
        recommendation = RESOLUTION_MAP["Too early to resolve"]
    print("recommendation:", recommendation)