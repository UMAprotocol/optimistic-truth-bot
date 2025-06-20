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
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-proxy/mlb"

# Resolution map
RESOLUTION_MAP = {
    "Athletics": "p2",
    "Angels": "p1",
    "50-50": "p3",
    "Too early to resolve": "p4"
}

# Helper function to make API requests
def make_api_request(endpoint, path):
    try:
        response = requests.get(f"{endpoint}/{path}", headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        return None

# Main function to determine the outcome of the game
def resolve_mlb_game():
    date_str = "2025-06-11"
    teams = ("Athletics", "Angels")
    game_date = datetime.strptime(date_str, "%Y-%m-%d").date()

    # Try proxy endpoint first
    games = make_api_request(PROXY_ENDPOINT, f"GamesByDate/{game_date}")
    if not games:
        # Fallback to primary endpoint
        games = make_api_request(PRIMARY_ENDPOINT, f"GamesByDate/{game_date}")

    if not games:
        return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

    for game in games:
        if {game["HomeTeam"], game["AwayTeam"]} == set(teams):
            if game["Status"] == "Final":
                home_team_wins = game["HomeTeamRuns"] > game["AwayTeamRuns"]
                away_team_wins = game["AwayTeamRuns"] > game["HomeTeamRuns"]
                if home_team_wins:
                    return "recommendation: " + RESOLUTION_MAP[game["HomeTeam"]]
                elif away_team_wins:
                    return "recommendation: " + RESOLUTION_MAP[game["AwayTeam"]]
            elif game["Status"] in ["Canceled", "Postponed"]:
                return "recommendation: " + RESOLUTION_MAP["50-50"]
            else:
                return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

    return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

# Execute the function and print the result
if __name__ == "__main__":
    result = resolve_mlb_game()
    print(result)