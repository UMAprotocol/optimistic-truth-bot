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
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/nhl-proxy"

# Resolution map based on the team abbreviations
RESOLUTION_MAP = {
    "SPI": "p2",  # Spirit
    "MOU": "p1",  # MOUZ
    "50-50": "p3",
    "Too early to resolve": "p4",
}

# Function to make API requests
def make_request(url, headers):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

# Function to find the game and determine the outcome
def find_game_and_determine_outcome():
    date_of_game = "2025-06-19"
    team1 = "SPI"
    team2 = "MOU"

    # Construct URL for the game day
    url = f"{PRIMARY_ENDPOINT}/scores/json/GamesByDate/{date_of_game}"
    games = make_request(url, HEADERS)

    if games is None:
        print("Failed to retrieve data from primary endpoint, trying proxy...")
        url = f"{PROXY_ENDPOINT}/scores/json/GamesByDate/{date_of_game}"
        games = make_request(url, HEADERS)
        if games is None:
            return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

    # Search for the specific game
    for game in games:
        if {game["HomeTeam"], game["AwayTeam"]} == {team1, team2}:
            if game["Status"] == "Final":
                if game["HomeTeam"] == team1 and game["HomeTeamRuns"] > game["AwayTeamRuns"]:
                    return "recommendation: " + RESOLUTION_MAP[team1]
                elif game["AwayTeam"] == team1 and game["AwayTeamRuns"] > game["HomeTeamRuns"]:
                    return "recommendation: " + RESOLUTION_MAP[team1]
                else:
                    return "recommendation: " + RESOLUTION_MAP[team2]
            elif game["Status"] in ["Canceled", "Postponed"]:
                return "recommendation: " + RESOLUTION_MAP["50-50"]
            else:
                return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]
    return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

# Main execution
if __name__ == "__main__":
    result = find_game_and_determine_outcome()
    print(result)