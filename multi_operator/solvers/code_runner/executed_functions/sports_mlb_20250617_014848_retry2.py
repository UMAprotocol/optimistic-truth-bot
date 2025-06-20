import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# Configuration for headers and endpoints
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/mlb/scores/json"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/mlb-proxy"

# Resolution map based on the game outcome
RESOLUTION_MAP = {
    "Orioles": "p2",
    "Rays": "p1",
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
def resolve_game(date_str, team1, team2):
    # Try proxy endpoint first
    games = make_request(PROXY_ENDPOINT, f"GamesByDate/{date_str}")
    if games is None:
        # Fallback to primary endpoint
        games = make_request(PRIMARY_ENDPOINT, f"GamesByDate/{date_str}")
    
    if games is None:
        return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

    for game in games:
        if {game["HomeTeam"], game["AwayTeam"]} == {team1, team2}:
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

# Main execution function
if __name__ == "__main__":
    # Game details
    date_of_game = "2025-06-16"
    home_team = "Rays"
    away_team = "Orioles"

    # Convert date to required format
    game_date = datetime.strptime(date_of_game, "%Y-%m-%d").strftime("%Y-%m-%d")

    # Resolve the game based on the outcome
    result = resolve_game(game_date, home_team, away_team)
    print(result)