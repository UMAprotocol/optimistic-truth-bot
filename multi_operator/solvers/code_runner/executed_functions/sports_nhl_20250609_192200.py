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
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-nhl-proxy"

# Resolution map based on the team abbreviations
RESOLUTION_MAP = {
    "FLA": "p2",  # Florida Panthers
    "CAR": "p1",  # Carolina Hurricanes
    "50-50": "p3",
    "Too early to resolve": "p4",
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

# Function to find the game and determine the outcome
def find_game_and_determine_outcome(date_str):
    # Try proxy endpoint first
    games = make_request(PROXY_ENDPOINT, f"GamesByDate/{date_str}")
    if games is None:
        # Fallback to primary endpoint
        games = make_request(PRIMARY_ENDPOINT, f"GamesByDate/{date_str}")
    
    if games is None:
        return "p4"  # Unable to resolve due to API failure

    for game in games:
        if {game["HomeTeam"], game["AwayTeam"]} == {"FLA", "CAR"}:
            if game["Status"] == "Final":
                if game["HomeTeam"] == "FLA" and game["HomeTeamScore"] > game["AwayTeamScore"]:
                    return RESOLUTION_MAP["FLA"]
                elif game["AwayTeam"] == "FLA" and game["AwayTeamScore"] > game["HomeTeamScore"]:
                    return RESOLUTION_MAP["FLA"]
                elif game["HomeTeam"] == "CAR" and game["HomeTeamScore"] > game["AwayTeamScore"]:
                    return RESOLUTION_MAP["CAR"]
                elif game["AwayTeam"] == "CAR" and game["AwayTeamScore"] > game["HomeTeamScore"]:
                    return RESOLUTION_MAP["CAR"]
            elif game["Status"] == "Postponed":
                return "p4"  # Market remains open
            elif game["Status"] == "Canceled":
                return RESOLUTION_MAP["50-50"]
    return "p4"  # Game not found or not yet played

# Main execution function
if __name__ == "__main__":
    game_date = "2025-05-28"
    recommendation = find_game_and_determine_outcome(game_date)
    print(f"recommendation: {recommendation}")