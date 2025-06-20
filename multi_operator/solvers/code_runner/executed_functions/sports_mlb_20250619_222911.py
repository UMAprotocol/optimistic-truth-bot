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
GAME_DATE = "2025-06-19"
HOME_TEAM = "San Francisco Giants"
AWAY_TEAM = "Cleveland Guardians"

# Resolution map based on the game outcome
RESOLUTION_MAP = {
    HOME_TEAM: "p1",  # Home team wins
    AWAY_TEAM: "p2",  # Away team wins
    "50-50": "p3",    # Game canceled or tie
    "Too early to resolve": "p4"  # Not enough data or game not completed
}

# Function to make API requests
def make_api_request(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"API request error: {e}")
        return None

# Function to find the game and determine the outcome
def find_game_and_determine_outcome():
    # Format the date for the API endpoint
    formatted_date = datetime.strptime(GAME_DATE, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{formatted_date}"
    games = make_api_request(url)

    if not games:
        return "Too early to resolve"

    # Search for the specific game
    for game in games:
        if game['HomeTeam'] == HOME_TEAM and game['AwayTeam'] == AWAY_TEAM:
            if game['Status'] == "Final":
                home_score = game['HomeTeamRuns']
                away_score = game['AwayTeamRuns']
                if home_score > away_score:
                    return RESOLUTION_MAP[HOME_TEAM]
                elif away_score > home_score:
                    return RESOLUTION_MAP[AWAY_TEAM]
            elif game['Status'] in ["Canceled", "Postponed"]:
                return RESOLUTION_MAP["50-50"]
            else:
                return RESOLUTION_MAP["Too early to resolve"]

    return RESOLUTION_MAP["Too early to resolve"]

# Main function to run the program
if __name__ == "__main__":
    result = find_game_and_determine_outcome()
    print(f"recommendation: {result}")