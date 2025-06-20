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
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nhl"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

# Resolution map based on the team abbreviations
RESOLUTION_MAP = {
    "EDM": "p2",  # Edmonton Oilers
    "FLA": "p1",  # Florida Panthers
    "50-50": "p3",
    "Too early to resolve": "p4",
}

# Function to make API requests with fallback to proxy
def make_api_request(endpoint, params=None):
    try:
        response = requests.get(f"{PROXY_ENDPOINT}{endpoint}", headers=HEADERS, params=params, timeout=10)
        if not response.ok:
            response = requests.get(f"{PRIMARY_ENDPOINT}{endpoint}", headers=HEADERS, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Failed to retrieve data: {e}")
        return None

# Function to determine the outcome of the game
def determine_outcome(game_date, team1, team2):
    date_str = datetime.strptime(game_date, "%Y-%m-%d").strftime("%Y-%m-%d")
    games = make_api_request(f"/scores/json/GamesByDate/{date_str}")

    if games:
        for game in games:
            if {game["HomeTeam"], game["AwayTeam"]} == {team1, team2}:
                if game["Status"] == "Final":
                    if game["HomeTeam"] == team1 and game["HomeTeamScore"] > game["AwayTeamScore"]:
                        return RESOLUTION_MAP[team1]
                    elif game["AwayTeam"] == team1 and game["AwayTeamScore"] > game["HomeTeamScore"]:
                        return RESOLUTION_MAP[team1]
                    elif game["HomeTeam"] == team2 and game["HomeTeamScore"] > game["AwayTeamScore"]:
                        return RESOLUTION_MAP[team2]
                    elif game["AwayTeam"] == team2 and game["AwayTeamScore"] > game["HomeTeamScore"]:
                        return RESOLUTION_MAP[team2]
                elif game["Status"] == "Postponed":
                    return RESOLUTION_MAP["Too early to resolve"]
                elif game["Status"] == "Canceled":
                    return RESOLUTION_MAP["50-50"]
    return RESOLUTION_MAP["Too early to resolve"]

# Main execution function
if __name__ == "__main__":
    game_date = "2025-06-09"
    team1 = "EDM"  # Edmonton Oilers
    team2 = "FLA"  # Florida Panthers
    result = determine_outcome(game_date, team1, team2)
    print(f"recommendation: {result}")