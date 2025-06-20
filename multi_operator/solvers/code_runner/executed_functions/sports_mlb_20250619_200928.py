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
    "Rockies": "p2",
    "Nationals": "p1",
    "50-50": "p3",
    "Too early to resolve": "p4"
}

# Helper function to make API requests
def make_api_request(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

# Function to find and resolve the game outcome
def resolve_game(date_str, team1, team2):
    formatted_date = datetime.strptime(date_str, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = f"{PROXY_ENDPOINT}/GamesByDate/{formatted_date}"
    games = make_api_request(url)
    if not games:
        url = f"{PRIMARY_ENDPOINT}/GamesByDate/{formatted_date}"
        games = make_api_request(url)
    if games:
        for game in games:
            if game["HomeTeam"] == team1 and game["AwayTeam"] == team2:
                if game["Status"] == "Final":
                    if game["HomeTeamRuns"] > game["AwayTeamRuns"]:
                        return RESOLUTION_MAP[team1]
                    elif game["HomeTeamRuns"] < game["AwayTeamRuns"]:
                        return RESOLUTION_MAP[team2]
                elif game["Status"] == "Canceled":
                    return RESOLUTION_MAP["50-50"]
                elif game["Status"] == "Postponed":
                    return RESOLUTION_MAP["Too early to resolve"]
    return RESOLUTION_MAP["Too early to resolve"]

# Main execution
if __name__ == "__main__":
    game_date = "2025-06-19"
    home_team = "Nationals"
    away_team = "Rockies"
    result = resolve_game(game_date, home_team, away_team)
    print(f"recommendation: {result}")