import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NHL_API_KEY")

# Constants
DATE = "2025-05-24"
TEAM1 = "USA"  # p1
TEAM2 = "SWE"  # p2
RESOLUTION_MAP = {
    "USA": "p1",
    "SWE": "p2",
    "50-50": "p3",
    "Too early to resolve": "p4",
}
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-nhl-proxy"
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nhl"

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
def find_game_and_determine_outcome(date, team1, team2):
    formatted_date = datetime.strptime(date, "%Y-%m-%d").date()
    url = f"{PRIMARY_ENDPOINT}/scores/json/GamesByDate/{formatted_date}"
    games = make_request(url, HEADERS)
    if games:
        for game in games:
            if {game["HomeTeam"], game["AwayTeam"]} == {team1, team2}:
                if game["Status"] == "Final":
                    winner = game["HomeTeam"] if game["HomeTeamRuns"] > game["AwayTeamRuns"] else game["AwayTeam"]
                    return RESOLUTION_MAP.get(winner, "p4")
                elif game["Status"] in ["Canceled", "Postponed"]:
                    return RESOLUTION_MAP["50-50"]
                else:
                    return RESOLUTION_MAP["Too early to resolve"]
    return RESOLUTION_MAP["Too early to resolve"]

# Main execution
if __name__ == "__main__":
    result = find_game_and_determine_outcome(DATE, TEAM1, TEAM2)
    print(f"recommendation: {result}")