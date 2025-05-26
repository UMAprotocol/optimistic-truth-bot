import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NHL_API_KEY")

# Constants
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
DATE = "2025-05-24"
TEAM1 = "DEL"  # Delhi Capitals
TEAM2 = "PBKS"  # Punjab Kings
RESOLUTION_MAP = {
    TEAM1: "p2",  # Delhi Capitals win
    TEAM2: "p1",  # Punjab Kings win
    "50-50": "p3",  # Game canceled
    "Too early to resolve": "p4",  # Game not yet played or in progress
}

# API Endpoints
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/nhl-proxy/GamesByDate/"

# Function to make API requests
def make_request(date):
    url = f"{PROXY_ENDPOINT}{date}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if not response.ok:
            # Fallback to primary endpoint if proxy fails
            url = f"{PRIMARY_ENDPOINT}{date}"
            response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

# Function to determine the outcome of the game
def determine_outcome(games):
    for game in games:
        if {game["HomeTeam"], game["AwayTeam"]} == {TEAM1, TEAM2}:
            if game["Status"] == "Final":
                home_score = game["HomeTeamRuns"]
                away_score = game["AwayTeamRuns"]
                if home_score > away_score:
                    winner = game["HomeTeam"]
                else:
                    winner = game["AwayTeam"]
                return RESOLUTION_MAP.get(winner, "Too early to resolve")
            elif game["Status"] in ["Canceled", "Postponed"]:
                return "50-50"
            else:
                return "Too early to resolve"
    return "Too early to resolve"

# Main function to run the program
def main():
    games = make_request(DATE)
    if games is None:
        print("recommendation: p4")  # Unable to retrieve data
    else:
        result = determine_outcome(games)
        print(f"recommendation: {result}")

if __name__ == "__main__":
    main()