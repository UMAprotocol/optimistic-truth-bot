import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NBA_API_KEY")

# Configuration for headers and endpoints
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nba"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-nba-proxy"

# Resolution map based on the ancillary data provided
RESOLUTION_MAP = {
    "OKC": "p2",  # Oklahoma City Thunder
    "MIN": "p1",  # Minnesota Timberwolves
    "50-50": "p3",
    "Too early to resolve": "p4",
}

# Function to make API requests
def make_request(endpoint, path):
    url = f"{endpoint}{path}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

# Function to find the game and determine the outcome
def find_game_and_resolve(date_str):
    # Format the date for the API endpoint
    formatted_date = datetime.strptime(date_str, "%Y-%m-%d").strftime("%Y-%m-%d")
    path = f"/scores/json/GamesByDate/{formatted_date}"

    # Try proxy endpoint first
    games = make_request(PROXY_ENDPOINT, path)
    if games is None:
        # Fallback to primary endpoint if proxy fails
        games = make_request(PRIMARY_ENDPOINT, path)
        if games is None:
            return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

    # Search for the specific game
    for game in games:
        if {game["HomeTeam"], game["AwayTeam"]} == {"OKC", "MIN"}:
            if game["Status"] == "Final":
                if game["HomeTeam"] == "OKC" and game["HomeTeamScore"] > game["AwayTeamScore"]:
                    return "recommendation: " + RESOLUTION_MAP["OKC"]
                elif game["AwayTeam"] == "OKC" and game["AwayTeamScore"] > game["HomeTeamScore"]:
                    return "recommendation: " + RESOLUTION_MAP["OKC"]
                else:
                    return "recommendation: " + RESOLUTION_MAP["MIN"]
            elif game["Status"] in ["Canceled", "Postponed"]:
                return "recommendation: " + RESOLUTION_MAP["50-50"]
            else:
                return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]
    return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

# Main execution function
if __name__ == "__main__":
    game_date = "2025-05-26"
    result = find_game_and_resolve(game_date)
    print(result)