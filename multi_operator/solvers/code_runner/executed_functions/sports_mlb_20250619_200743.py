import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# Constants
DATE = "2025-06-19"
TEAM1 = "Washington Nationals"  # Corresponds to p1
TEAM2 = "Colorado Rockies"      # Corresponds to p2
RESOLUTION_MAP = {
    TEAM1: "p1",
    TEAM2: "p2",
    "Postponed": "p4",
    "Canceled": "p3",
    "50-50": "p3"
}

# API Configuration
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/mlb-proxy/GamesByDate/"

# Function to make API requests
def make_api_request(date):
    url = f"{PRIMARY_ENDPOINT}{date}"
    proxy_url = f"{PROXY_ENDPOINT}{date}"
    try:
        response = requests.get(proxy_url, headers=HEADERS, timeout=10)
        if not response.ok:
            raise Exception("Proxy failed")
        return response.json()
    except:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.ok:
            return response.json()
        response.raise_for_status()

# Function to determine the outcome
def determine_outcome(games):
    for game in games:
        if {game["HomeTeam"], game["AwayTeam"]} == {TEAM1, TEAM2}:
            if game["Status"] == "Final":
                home_runs = game["HomeTeamRuns"]
                away_runs = game["AwayTeamRuns"]
                if home_runs > away_runs:
                    winner = game["HomeTeam"]
                else:
                    winner = game["AwayTeam"]
                return RESOLUTION_MAP.get(winner, "p3")
            elif game["Status"] in ["Postponed", "Canceled"]:
                return RESOLUTION_MAP[game["Status"]]
    return "p4"  # No game found or in progress

# Main execution
if __name__ == "__main__":
    games = make_api_request(DATE)
    result = determine_outcome(games)
    print(f"recommendation: {result}")