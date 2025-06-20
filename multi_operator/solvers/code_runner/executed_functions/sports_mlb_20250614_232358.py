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
    "Cardinals": "p2",
    "Brewers": "p1",
    "50-50": "p3",
    "Too early to resolve": "p4"
}

# Helper function to make API requests
def make_api_request(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        # Fallback to proxy if primary fails
        try:
            proxy_url = PROXY_ENDPOINT + url[len(PRIMARY_ENDPOINT):]
            response = requests.get(proxy_url, headers=HEADERS, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error accessing API through primary and proxy: {str(e)}")
            return None

# Function to determine the outcome of the game
def determine_outcome(game_date, home_team, away_team):
    date_str = game_date.strftime("%Y-%m-%d")
    games_today = make_api_request(f"{PRIMARY_ENDPOINT}/GamesByDate/{date_str}")

    if games_today is None:
        return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

    for game in games_today:
        if game["HomeTeam"] == home_team and game["AwayTeam"] == away_team:
            if game["Status"] == "Final":
                home_score = game["HomeTeamRuns"]
                away_score = game["AwayTeamRuns"]
                if home_score > away_score:
                    return "recommendation: " + RESOLUTION_MAP[home_team]
                elif away_score > home_score:
                    return "recommendation: " + RESOLUTION_MAP[away_team]
            elif game["Status"] == "Canceled":
                return "recommendation: " + RESOLUTION_MAP["50-50"]
            elif game["Status"] == "Postponed":
                return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]
    return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

# Main execution
if __name__ == "__main__":
    game_date = datetime.strptime("2025-06-14", "%Y-%m-%d")
    home_team = "Brewers"
    away_team = "Cardinals"
    print(determine_outcome(game_date, home_team, away_team))