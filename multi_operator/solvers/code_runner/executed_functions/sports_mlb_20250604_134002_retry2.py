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
    "Athletics": "p2",
    "Blue Jays": "p1",
    "50-50": "p3",
    "Too early to resolve": "p4"
}

# Function to make API requests
def make_api_request(endpoint, path):
    try:
        response = requests.get(f"{PROXY_ENDPOINT}/{path}", headers=HEADERS, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception("Proxy failed")
    except:
        response = requests.get(f"{PRIMARY_ENDPOINT}/{path}", headers=HEADERS, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            response.raise_for_status()

# Function to determine the outcome of the game
def determine_outcome(game_date, home_team, away_team):
    date_formatted = datetime.strptime(game_date, "%Y-%m-%d").strftime("%Y-%m-%d")
    games_today = make_api_request(PRIMARY_ENDPOINT, f"GamesByDate/{date_formatted}")

    for game in games_today:
        if game["HomeTeam"] == home_team and game["AwayTeam"] == away_team:
            if game["Status"] == "Final":
                home_score = game["HomeTeamRuns"]
                away_score = game["AwayTeamRuns"]
                if home_score > away_score:
                    return RESOLUTION_MAP[home_team]
                elif away_score > home_score:
                    return RESOLUTION_MAP[away_team]
            elif game["Status"] == "Canceled":
                return RESOLUTION_MAP["50-50"]
            elif game["Status"] == "Postponed":
                return RESOLUTION_MAP["Too early to resolve"]
    return RESOLUTION_MAP["Too early to resolve"]

# Main execution
if __name__ == "__main__":
    game_date = "2025-05-31"
    home_team = "Blue Jays"
    away_team = "Athletics"
    result = determine_outcome(game_date, home_team, away_team)
    print(f"recommendation: {result}")