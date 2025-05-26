import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NHL_API_KEY")

# Configuration for API requests
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nhl/scores/json"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/nhl-proxy"

# Resolution map based on the ancillary data provided
RESOLUTION_MAP = {
    "CAR": "p2",  # Carolina Hurricanes
    "FLA": "p1",  # Florida Panthers
    "50-50": "p3",
    "Too early to resolve": "p4",
}

# Function to make API requests with fallback to proxy
def make_api_request(endpoint, path):
    try:
        response = requests.get(f"{PROXY_ENDPOINT}{path}", headers=HEADERS, timeout=10)
        if not response.ok:
            raise Exception("Proxy failed")
        return response.json()
    except:
        response = requests.get(f"{PRIMARY_ENDPOINT}{path}", headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()

# Function to find the game and determine the outcome
def resolve_nhl_game(date_str):
    games_today = make_api_request(PRIMARY_ENDPOINT, f"/GamesByDate/{date_str}")
    for game in games_today:
        if {game["HomeTeam"], game["AwayTeam"]} == {"CAR", "FLA"}:
            if game["Status"] == "Final":
                if game["HomeTeam"] == "CAR" and game["HomeTeamScore"] > game["AwayTeamScore"]:
                    return RESOLUTION_MAP["CAR"]
                elif game["AwayTeam"] == "CAR" and game["AwayTeamScore"] > game["HomeTeamScore"]:
                    return RESOLUTION_MAP["CAR"]
                else:
                    return RESOLUTION_MAP["FLA"]
            elif game["Status"] in ["Canceled", "Postponed"]:
                return RESOLUTION_MAP["50-50"]
            else:
                return RESOLUTION_MAP["Too early to resolve"]
    return RESOLUTION_MAP["Too early to resolve"]

# Main execution logic
if __name__ == "__main__":
    game_date = "2025-05-24"
    print("recommendation:", resolve_nhl_game(game_date))