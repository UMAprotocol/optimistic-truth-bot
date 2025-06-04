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
DATE = "2025-05-30"
TEAM1 = "Colorado Rockies"
TEAM2 = "New York Mets"
RESOLUTION_MAP = {
    "Rockies": "p2",
    "Mets": "p1",
    "50-50": "p3",
    "Too early to resolve": "p4"
}

# Function to make API requests
def make_request(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error during request: {e}")
        return None

# Function to find the game and determine the outcome
def find_game_and_resolve():
    # Format the date for the API request
    formatted_date = datetime.strptime(DATE, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = f"https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/{formatted_date}"
    games = make_request(url)

    if not games:
        return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

    for game in games:
        if game["HomeTeam"] == TEAM1 and game["AwayTeam"] == TEAM2 or \
           game["HomeTeam"] == TEAM2 and game["AwayTeam"] == TEAM1:
            if game["Status"] == "Final":
                home_team_wins = game["HomeTeamRuns"] > game["AwayTeamRuns"]
                if home_team_wins:
                    winner = game["HomeTeam"]
                else:
                    winner = game["AwayTeam"]
                return "recommendation: " + RESOLUTION_MAP[winner]
            elif game["Status"] == "Postponed":
                return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]
            elif game["Status"] == "Canceled":
                return "recommendation: " + RESOLUTION_MAP["50-50"]
    
    return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

# Main execution
if __name__ == "__main__":
    result = find_game_and_resolve()
    print(result)