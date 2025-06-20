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
    "Angels": "p1",
    "50-50": "p3",
    "Too early to resolve": "p4"
}

# Helper function to make API requests
def make_api_request(url, use_proxy=False):
    endpoint = PROXY_ENDPOINT if use_proxy else PRIMARY_ENDPOINT
    full_url = f"{endpoint}{url}"
    try:
        response = requests.get(full_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if use_proxy:
            print("Proxy failed, trying primary endpoint.")
            return make_api_request(url, use_proxy=False)
        else:
            print(f"API request failed: {e}")
            return None

# Function to determine the outcome of the game
def determine_outcome(game_date, home_team, away_team):
    date_str = datetime.strptime(game_date, "%Y-%m-%d").strftime("%Y-%m-%d")
    games = make_api_request(f"/GamesByDate/{date_str}")

    if games is None:
        return "Too early to resolve"

    for game in games:
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
                return "Too early to resolve"

    return "Too early to resolve"

# Main execution
if __name__ == "__main__":
    game_date = "2025-06-10"
    home_team = "Angels"
    away_team = "Athletics"
    result = determine_outcome(game_date, home_team, away_team)
    print(f"recommendation: {result}")