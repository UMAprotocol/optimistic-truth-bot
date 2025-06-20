import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NHL_API_KEY")

# Configuration for API requests
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nhl/scores/json"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-nhl-proxy"

# Resolution map based on the ancillary data provided
RESOLUTION_MAP = {
    "EDM": "p2",  # Edmonton Oilers
    "FLA": "p1",  # Florida Panthers
    "50-50": "p3",
    "Too early to resolve": "p4",
}

# Function to make API requests
def make_request(endpoint, path):
    try:
        response = requests.get(f"{endpoint}{path}", headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return None

# Function to find the game and determine the outcome
def find_game_and_resolve(date_str):
    # Try proxy endpoint first
    games = make_request(PROXY_ENDPOINT, f"/GamesByDate/{date_str}")
    if games is None:
        # Fallback to primary endpoint
        games = make_request(PRIMARY_ENDPOINT, f"/GamesByDate/{date_str}")
        if games is None:
            return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

    # Search for the specific game
    for game in games:
        if {game["HomeTeam"], game["AwayTeam"]} == {"EDM", "FLA"}:
            if game["Status"] == "Final":
                if game["HomeTeamRuns"] > game["AwayTeamRuns"]:
                    winner = game["HomeTeam"]
                else:
                    winner = game["AwayTeam"]
                return "recommendation: " + RESOLUTION_MAP[winner]
            elif game["Status"] in ["Canceled", "Postponed"]:
                return "recommendation: " + RESOLUTION_MAP["50-50"]
            else:
                return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

    return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

# Main execution
if __name__ == "__main__":
    game_date = "2025-06-12"
    print(find_game_and_resolve(game_date))