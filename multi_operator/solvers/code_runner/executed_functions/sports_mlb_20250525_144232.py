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
GAME_DATE = "2025-05-25"
TEAM1 = "Chennai Super Kings"
TEAM2 = "Gujarat Titans"

# Resolution map based on the game outcome
RESOLUTION_MAP = {
    TEAM1: "p1",
    TEAM2: "p2",
    "Postponed": "p4",
    "Canceled": "p3",
    "Unknown": "p3"
}

# Function to make a GET request to the API
def get_api_data(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"API request error: {e}")
        return None

# Function to find the game and determine the outcome
def find_game_and_resolve():
    date_formatted = datetime.strptime(GAME_DATE, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{date_formatted}"
    games = get_api_data(url)
    
    if not games:
        return "p4"  # Unable to retrieve data, assume in-progress

    for game in games:
        if {game["HomeTeam"], game["AwayTeam"]} == {TEAM1, TEAM2}:
            if game["Status"] == "Final":
                if game["HomeTeamRuns"] > game["AwayTeamRuns"]:
                    winner = game["HomeTeam"]
                else:
                    winner = game["AwayTeam"]
                return RESOLUTION_MAP.get(winner, "p3")
            elif game["Status"] in ["Postponed", "Canceled"]:
                return RESOLUTION_MAP[game["Status"]]
            else:
                return "p4"  # Game not final

    return "p4"  # No matching game found or game not yet played

# Main execution
if __name__ == "__main__":
    recommendation = find_game_and_resolve()
    print(f"recommendation: {recommendation}")