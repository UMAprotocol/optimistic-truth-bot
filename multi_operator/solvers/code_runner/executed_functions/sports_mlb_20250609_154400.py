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
GAME_DATE = "2025-06-08"
HOME_TEAM = "San Francisco Giants"
AWAY_TEAM = "Atlanta Braves"

# Resolution map based on the game outcome
RESOLUTION_MAP = {
    HOME_TEAM: "p1",  # Home team wins
    AWAY_TEAM: "p2",  # Away team wins
    "Postponed": "p4",  # Game postponed
    "Canceled": "p3",  # Game canceled
    "Scheduled": "p4"  # Game scheduled but not yet played
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

# Function to find the game and determine its outcome
def find_game_and_determine_outcome():
    date_formatted = datetime.strptime(GAME_DATE, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{date_formatted}"
    games = make_api_request(url)
    
    if not games:
        return "p4"  # Unable to retrieve data

    for game in games:
        if game["HomeTeam"] == HOME_TEAM and game["AwayTeam"] == AWAY_TEAM:
            if game["Status"] == "Final":
                if game["HomeTeamRuns"] > game["AwayTeamRuns"]:
                    return RESOLUTION_MAP[HOME_TEAM]
                elif game["HomeTeamRuns"] < game["AwayTeamRuns"]:
                    return RESOLUTION_MAP[AWAY_TEAM]
            elif game["Status"] in ["Postponed", "Canceled"]:
                return RESOLUTION_MAP[game["Status"]]
            else:
                return RESOLUTION_MAP["Scheduled"]
    
    return "p4"  # Game not found or no conclusive outcome

# Main execution function
if __name__ == "__main__":
    recommendation = find_game_and_determine_outcome()
    print(f"recommendation: {recommendation}")