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
    "DAL": "p2",  # Dallas Stars
    "EDM": "p1",  # Edmonton Oilers
    "50-50": "p3",
    "Too early to resolve": "p4",
}

# Function to make API requests with fallback to proxy
def make_api_request(endpoint, path):
    url = f"{endpoint}{path}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        if endpoint == PRIMARY_ENDPOINT:
            return make_api_request(PROXY_ENDPOINT, path)
        else:
            return None

# Function to find the game and determine the outcome
def find_game_and_determine_outcome(date, team1, team2):
    path = f"/GamesByDate/{date}"
    games = make_api_request(PRIMARY_ENDPOINT, path)
    if not games:
        return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

    for game in games:
        if {game["HomeTeam"], game["AwayTeam"]} == {team1, team2}:
            if game["Status"] == "Final":
                if game["HomeTeam"] == team1 and game["HomeTeamRuns"] > game["AwayTeamRuns"]:
                    return "recommendation: " + RESOLUTION_MAP[team1]
                elif game["AwayTeam"] == team1 and game["AwayTeamRuns"] > game["HomeTeamRuns"]:
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
    game_date = "2025-05-27"
    team1 = "EDM"  # Edmonton Oilers
    team2 = "DAL"  # Dallas Stars
    print(find_game_and_determine_outcome(game_date, team1, team2))