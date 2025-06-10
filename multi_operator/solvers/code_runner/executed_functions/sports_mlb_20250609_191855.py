import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# API configuration
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/mlb/scores/json"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

# Game details
GAME_DATE = "2025-06-01"
TEAM1 = "STL"  # St. Louis Cardinals
TEAM2 = "TEX"  # Texas Rangers

# Function to make API requests
def make_request(endpoint, path):
    try:
        response = requests.get(f"{endpoint}/{path}", headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

# Function to find the game and determine the outcome
def find_game_and_outcome():
    date_formatted = datetime.strptime(GAME_DATE, "%Y-%m-%d").strftime("%Y-%m-%d")
    games = make_request(PRIMARY_ENDPOINT, f"GamesByDate/{date_formatted}")
    if not games:
        games = make_request(PROXY_ENDPOINT, f"GamesByDate/{date_formatted}")
        if not games:
            return "p4"  # Unable to retrieve data

    for game in games:
        if game["HomeTeam"] == TEAM1 and game["AwayTeam"] == TEAM2:
            if game["Status"] == "Final":
                if game["HomeTeamRuns"] > game["AwayTeamRuns"]:
                    return "p2"  # Cardinals win
                elif game["HomeTeamRuns"] < game["AwayTeamRuns"]:
                    return "p1"  # Rangers win
            elif game["Status"] == "Canceled":
                return "p3"  # Game canceled
            elif game["Status"] == "Postponed":
                return "p4"  # Game postponed, check later
    return "p4"  # No game found or not yet played

# Main execution
if __name__ == "__main__":
    result = find_game_and_outcome()
    print(f"recommendation: {result}")