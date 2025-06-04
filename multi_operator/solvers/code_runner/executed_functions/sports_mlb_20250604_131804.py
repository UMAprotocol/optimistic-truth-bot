import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

# Constants
GAME_DATE = "2025-05-31"
HOME_TEAM = "Cubs"
AWAY_TEAM = "Reds"
RESOLUTION_MAP = {
    "Cubs": "p1",
    "Reds": "p2",
    "50-50": "p3",
    "Too early to resolve": "p4"
}

# Function to make API requests
def make_request(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

# Function to find the game and determine the outcome
def resolve_game():
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{GAME_DATE}"
    games = make_request(url)
    if not games:
        return RESOLUTION_MAP["Too early to resolve"]

    for game in games:
        if game["HomeTeam"] == HOME_TEAM and game["AwayTeam"] == AWAY_TEAM:
            if game["Status"] == "Final":
                home_score = game["HomeTeamRuns"]
                away_score = game["AwayTeamRuns"]
                if home_score > away_score:
                    return RESOLUTION_MAP[HOME_TEAM]
                elif away_score > home_score:
                    return RESOLUTION_MAP[AWAY_TEAM]
            elif game["Status"] == "Canceled":
                return RESOLUTION_MAP["50-50"]
            elif game["Status"] == "Postponed":
                return RESOLUTION_MAP["Too early to resolve"]
    return RESOLUTION_MAP["Too early to resolve"]

# Main execution
if __name__ == "__main__":
    result = resolve_game()
    print(f"recommendation: {result}")