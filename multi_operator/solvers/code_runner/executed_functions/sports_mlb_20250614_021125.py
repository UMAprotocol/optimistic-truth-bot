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
    "Yankees": "p2",
    "Red Sox": "p1",
    "50-50": "p3",
    "Too early to resolve": "p4"
}

# Function to make API requests
def make_request(endpoint, path):
    try:
        response = requests.get(f"{endpoint}/{path}", headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

# Function to determine the outcome of the game
def determine_outcome(game_date, home_team, away_team):
    date_str = datetime.strptime(game_date, "%Y-%m-%d").strftime("%Y-%m-%d")
    games_today = make_request(PROXY_ENDPOINT, f"GamesByDate/{date_str}")
    if not games_today:
        games_today = make_request(PRIMARY_ENDPOINT, f"GamesByDate/{date_str}")

    if games_today:
        for game in games_today:
            if game["HomeTeam"] == home_team and game["AwayTeam"] == away_team:
                if game["Status"] == "Final":
                    if game["HomeTeamRuns"] > game["AwayTeamRuns"]:
                        return RESOLUTION_MAP[home_team]
                    elif game["AwayTeamRuns"] > game["HomeTeamRuns"]:
                        return RESOLUTION_MAP[away_team]
                elif game["Status"] == "Canceled":
                    return RESOLUTION_MAP["50-50"]
                elif game["Status"] == "Postponed":
                    return RESOLUTION_MAP["Too early to resolve"]
    return RESOLUTION_MAP["Too early to resolve"]

# Main execution function
def main():
    game_date = "2025-06-13"
    home_team = "Red Sox"
    away_team = "Yankees"
    result = determine_outcome(game_date, home_team, away_team)
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()