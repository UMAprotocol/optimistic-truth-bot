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
    "Rangers": "p1",
    "Twins": "p2",
    "50-50": "p3",
    "Too early to resolve": "p4"
}

# Helper function to make API requests
def make_api_request(url, params=None):
    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

# Function to determine the outcome of the game
def determine_outcome(game_date, home_team, away_team):
    date_str = datetime.strptime(game_date, "%Y-%m-%d").strftime("%Y-%m-%d")
    games_today = make_api_request(f"{PRIMARY_ENDPOINT}/GamesByDate/{date_str}")

    if games_today is None:
        games_today = make_api_request(f"{PROXY_ENDPOINT}/GamesByDate/{date_str}")

    if not games_today:
        return RESOLUTION_MAP["Too early to resolve"]

    for game in games_today:
        if game["HomeTeam"] == home_team and game["AwayTeam"] == away_team:
            if game["Status"] == "Final":
                if game["HomeTeamRuns"] > game["AwayTeamRuns"]:
                    return RESOLUTION_MAP[home_team]
                elif game["HomeTeamRuns"] < game["AwayTeamRuns"]:
                    return RESOLUTION_MAP[away_team]
            elif game["Status"] in ["Canceled", "Postponed"]:
                return RESOLUTION_MAP["50-50"]
            else:
                return RESOLUTION_MAP["Too early to resolve"]

    return RESOLUTION_MAP["Too early to resolve"]

# Main function to run the program
def main():
    game_date = "2025-06-10"
    home_team = "Twins"
    away_team = "Rangers"
    result = determine_outcome(game_date, home_team, away_team)
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()