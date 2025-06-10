import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
MLB_API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not MLB_API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# API configuration
HEADERS = {"Ocp-Apim-Subscription-Key": MLB_API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/mlb/scores/json"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/mlb-proxy"

# Resolution map
RESOLUTION_MAP = {
    "Pirates": "p2",
    "Padres": "p1",
    "50-50": "p3"
}

# Helper function to make API requests
def make_request(endpoint, path):
    try:
        response = requests.get(f"{PROXY_ENDPOINT}/{path}", headers=HEADERS, timeout=10)
        if not response.ok:
            raise Exception("Proxy failed")
        return response.json()
    except:
        response = requests.get(f"{PRIMARY_ENDPOINT}/{path}", headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()

# Function to determine the outcome of the game
def determine_outcome(game_date, home_team, away_team):
    date_str = datetime.strptime(game_date, "%Y-%m-%d").strftime("%Y-%m-%d")
    games = make_request(PRIMARY_ENDPOINT, f"GamesByDate/{date_str}")

    for game in games:
        if game["HomeTeam"] == home_team and game["AwayTeam"] == away_team:
            if game["Status"] == "Final":
                home_score = game["HomeTeamRuns"]
                away_score = game["AwayTeamRuns"]
                if home_score > away_score:
                    return RESOLUTION_MAP[home_team]
                elif away_score > home_score:
                    return RESOLUTION_MAP[away_team]
            elif game["Status"] == "Canceled":
                return RESOLUTION_MAP["50-50"]
            elif game["Status"] == "Postponed":
                return "p4"  # Market remains open
    return "p4"  # No data available or game not yet played

# Main execution
if __name__ == "__main__":
    game_date = "2025-05-30"
    home_team = "Padres"
    away_team = "Pirates"
    result = determine_outcome(game_date, home_team, away_team)
    print(f"recommendation: {result}")