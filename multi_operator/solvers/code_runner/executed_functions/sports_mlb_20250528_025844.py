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
    "Athletics": "p2",
    "Astros": "p1",
    "Postponed": "p4",
    "Canceled": "p3",
    "50-50": "p3"
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
def find_game_and_determine_outcome(date_str):
    formatted_date = datetime.strptime(date_str, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = f"{PRIMARY_ENDPOINT}/GamesByDate/{formatted_date}"
    games = make_api_request(url)
    if games is None:
        print("Using proxy endpoint due to primary endpoint failure.")
        url = f"{PROXY_ENDPOINT}/GamesByDate/{formatted_date}"
        games = make_api_request(url)
        if games is None:
            return "p4"  # Unable to retrieve data

    for game in games:
        if game["HomeTeam"] == "HOU" and game["AwayTeam"] == "OAK":
            if game["Status"] == "Final":
                home_score = game["HomeTeamRuns"]
                away_score = game["AwayTeamRuns"]
                if home_score > away_score:
                    return RESOLUTION_MAP["Astros"]
                else:
                    return RESOLUTION_MAP["Athletics"]
            elif game["Status"] == "Postponed":
                return RESOLUTION_MAP["Postponed"]
            elif game["Status"] == "Canceled":
                return RESOLUTION_MAP["Canceled"]
    return "p4"  # Game not found or in progress

# Main execution
if __name__ == "__main__":
    game_date = "2025-05-27"
    result = find_game_and_determine_outcome(game_date)
    print(f"recommendation: {result}")