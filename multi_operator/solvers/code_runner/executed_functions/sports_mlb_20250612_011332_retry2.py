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

# Resolution map based on the outcomes
RESOLUTION_MAP = {
    "Tigers": "p2",
    "Orioles": "p1",
    "50-50": "p3",
    "Too early to resolve": "p4"
}

# Function to make API requests
def make_api_request(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

# Function to find and resolve the game outcome
def resolve_game(date, team1, team2):
    formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = f"{PRIMARY_ENDPOINT}/GamesByDate/{formatted_date}"
    games = make_api_request(url)
    if not games:
        print("Failed to retrieve data from primary endpoint, trying proxy...")
        url = f"{PROXY_ENDPOINT}/GamesByDate/{formatted_date}"
        games = make_api_request(url)
        if not games:
            return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

    for game in games:
        if game["HomeTeam"] == team1 and game["AwayTeam"] == team2:
            if game["Status"] == "Final":
                home_score = game["HomeTeamRuns"]
                away_score = game["AwayTeamRuns"]
                if home_score > away_score:
                    return "recommendation: " + RESOLUTION_MAP[team1]
                else:
                    return "recommendation: " + RESOLUTION_MAP[team2]
            elif game["Status"] == "Canceled":
                return "recommendation: " + RESOLUTION_MAP["50-50"]
            elif game["Status"] == "Postponed":
                return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]
    return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

# Main execution function
if __name__ == "__main__":
    game_date = "2025-06-11"
    home_team = "Tigers"
    away_team = "Orioles"
    result = resolve_game(game_date, home_team, away_team)
    print(result)