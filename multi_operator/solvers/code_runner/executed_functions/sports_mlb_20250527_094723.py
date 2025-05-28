import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# Configuration for headers and API endpoints
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/mlb/scores/json"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-proxy/mlb"

# Resolution map based on the game outcome
RESOLUTION_MAP = {
    "Red Sox": "p2",
    "Brewers": "p1",
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

# Function to find the game and determine the outcome
def resolve_game(date_str):
    formatted_date = datetime.strptime(date_str, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = f"{PROXY_ENDPOINT}/GamesByDate/{formatted_date}"
    games = make_api_request(url)
    if not games:
        url = f"{PRIMARY_ENDPOINT}/GamesByDate/{formatted_date}"
        games = make_api_request(url)
    if games:
        for game in games:
            if game["HomeTeam"] == "MIL" and game["AwayTeam"] == "BOS":
                if game["Status"] == "Final":
                    home_score = game["HomeTeamRuns"]
                    away_score = game["AwayTeamRuns"]
                    if home_score > away_score:
                        return RESOLUTION_MAP["Brewers"]
                    elif away_score > home_score:
                        return RESOLUTION_MAP["Red Sox"]
                elif game["Status"] == "Canceled":
                    return RESOLUTION_MAP["50-50"]
                elif game["Status"] == "Postponed":
                    return RESOLUTION_MAP["Too early to resolve"]
    return RESOLUTION_MAP["Too early to resolve"]

# Main execution function
if __name__ == "__main__":
    game_date = "2025-05-26"
    recommendation = resolve_game(game_date)
    print(f"recommendation: {recommendation}")