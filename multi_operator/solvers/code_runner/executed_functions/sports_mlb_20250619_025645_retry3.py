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
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/mlb-proxy"

# Resolution map
RESOLUTION_MAP = {
    "Royals": "p2",
    "Rangers": "p1",
    "50-50": "p3",
    "Too early to resolve": "p4"
}

# Function to make API requests
def make_request(endpoint, path):
    try:
        response = requests.get(f"{endpoint}/{path}", headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        return None

# Function to find and resolve the game outcome
def resolve_game(date, home_team, away_team):
    # Try proxy endpoint first
    games = make_request(PROXY_ENDPOINT, f"GamesByDate/{date}")
    if not games:
        # Fallback to primary endpoint
        games = make_request(PRIMARY_ENDPOINT, f"GamesByDate/{date}")
    
    if not games:
        return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

    for game in games:
        if game["HomeTeam"] == home_team and game["AwayTeam"] == away_team:
            if game["Status"] == "Final":
                home_score = game["HomeTeamRuns"]
                away_score = game["AwayTeamRuns"]
                if home_score > away_score:
                    return "recommendation: " + RESOLUTION_MAP[home_team]
                else:
                    return "recommendation: " + RESOLUTION_MAP[away_team]
            elif game["Status"] in ["Canceled", "Postponed"]:
                return "recommendation: " + RESOLUTION_MAP["50-50"]
    
    return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

# Main execution
if __name__ == "__main__":
    game_date = "2025-06-18"
    home_team = "Rangers"
    away_team = "Royals"
    print(resolve_game(game_date, home_team, away_team))