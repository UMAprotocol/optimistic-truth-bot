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
GAME_DATE = "2025-06-10"
HOME_TEAM = "Minnesota Twins"
AWAY_TEAM = "Texas Rangers"

# Function to make API requests
def make_request(endpoint, path):
    try:
        response = requests.get(f"{endpoint}/{path}", headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error during API request: {e}")
        return None

# Function to find the game and determine the outcome
def find_game_and_outcome():
    date_formatted = datetime.strptime(GAME_DATE, "%Y-%m-%d").strftime("%Y-%m-%d")
    games_today = make_request(PRIMARY_ENDPOINT, f"GamesByDate/{date_formatted}")

    if not games_today:
        return "p4"  # Unable to retrieve data

    for game in games_today:
        if game["HomeTeam"] == HOME_TEAM and game["AwayTeam"] == AWAY_TEAM:
            if game["Status"] == "Final":
                if game["HomeTeamRuns"] > game["AwayTeamRuns"]:
                    return "p1"  # Home team wins
                elif game["AwayTeamRuns"] > game["HomeTeamRuns"]:
                    return "p2"  # Away team wins
            elif game["Status"] == "Postponed":
                return "p4"  # Game postponed
            elif game["Status"] == "Canceled":
                return "p3"  # Game canceled

    return "p4"  # No matching game found or game not yet played

# Main execution
if __name__ == "__main__":
    result = find_game_and_outcome()
    print(f"recommendation: {result}")