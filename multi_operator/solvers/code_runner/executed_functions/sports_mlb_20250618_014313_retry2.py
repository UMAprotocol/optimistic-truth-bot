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
    "Angels": "p2",
    "Yankees": "p1",
    "50-50": "p3",
    "Too early to resolve": "p4"
}

# Helper function to make API requests
def make_request(endpoint, path):
    try:
        response = requests.get(f"{endpoint}/{path}", headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        return None

# Main function to determine the outcome
def resolve_mlb_game(date, team1, team2):
    # Format date for API request
    formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m-%d")
    games_today = make_request(PROXY_ENDPOINT, f"GamesByDate/{formatted_date}")

    if not games_today:
        games_today = make_request(PRIMARY_ENDPOINT, f"GamesByDate/{formatted_date}")
        if not games_today:
            return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

    # Find the specific game
    for game in games_today:
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

# Execute the function with the specific game details
if __name__ == "__main__":
    game_date = "2025-06-17"
    home_team = "Yankees"
    away_team = "Angels"
    print(resolve_mlb_game(game_date, home_team, away_team))