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
    "Guardians": "p2",
    "Mariners": "p1",
    "50-50": "p3",
    "Too early to resolve": "p4"
}

# Function to make API requests
def make_api_request(endpoint, path):
    try:
        response = requests.get(f"{endpoint}/{path}", headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        if endpoint == PROXY_ENDPOINT:
            return make_api_request(PRIMARY_ENDPOINT, path)
        else:
            return None

# Function to determine the outcome of the game
def determine_outcome(game_date, home_team, away_team):
    date_str = datetime.strptime(game_date, "%Y-%m-%d").strftime("%Y-%m-%d")
    games_today = make_api_request(PROXY_ENDPOINT, f"GamesByDate/{date_str}")

    if games_today is None:
        return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

    for game in games_today:
        if game["HomeTeam"] == home_team and game["AwayTeam"] == away_team:
            if game["Status"] == "Final":
                if game["HomeTeamRuns"] > game["AwayTeamRuns"]:
                    return "recommendation: " + RESOLUTION_MAP[home_team]
                elif game["HomeTeamRuns"] < game["AwayTeamRuns"]:
                    return "recommendation: " + RESOLUTION_MAP[away_team]
            elif game["Status"] == "Canceled":
                return "recommendation: " + RESOLUTION_MAP["50-50"]
            elif game["Status"] == "Postponed":
                return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]
            else:
                return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

    return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

# Main execution
if __name__ == "__main__":
    game_date = "2025-06-15"
    home_team = "Mariners"
    away_team = "Guardians"
    print(determine_outcome(game_date, home_team, away_team))