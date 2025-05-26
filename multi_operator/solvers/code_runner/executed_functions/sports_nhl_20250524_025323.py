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
    "DAL": "p1",  # Dallas Stars
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
def find_game_and_resolve(date_str, team1, team2):
    # Try proxy endpoint first
    games = make_request(PROXY_ENDPOINT, f"/GamesByDate/{date_str}")
    if games is None:
        # Fallback to primary endpoint
        games = make_request(PRIMARY_ENDPOINT, f"/GamesByDate/{date_str}")
        if games is None:
            return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

    # Search for the specific game
    for game in games:
        if {game["HomeTeam"], game["AwayTeam"]} == {team1, team2}:
            if game["Status"] == "Final":
                if game["HomeTeam"] == team1 and game["HomeTeamScore"] > game["AwayTeamScore"]:
                    return "recommendation: " + RESOLUTION_MAP[team1]
                elif game["AwayTeam"] == team1 and game["AwayTeamScore"] > game["HomeTeamScore"]:
                    return "recommendation: " + RESOLUTION_MAP[team1]
                else:
                    return "recommendation: " + RESOLUTION_MAP[team2]
            elif game["Status"] in ["Canceled", "Postponed"]:
                return "recommendation: " + RESOLUTION_MAP["50-50"]
            else:
                return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]
    return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

# Main execution function
if __name__ == "__main__":
    # Game details extracted from the question
    game_date = "2025-05-23"
    team1 = "DAL"  # Dallas Stars
    team2 = "EDM"  # Edmonton Oilers

    # Resolve the market based on the game outcome
    result = find_game_and_resolve(game_date, team1, team2)
    print(result)