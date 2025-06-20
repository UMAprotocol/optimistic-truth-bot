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
DATE = "2025-06-12"
TEAM1 = "EDM"  # Edmonton Oilers
TEAM2 = "FLA"  # Florida Panthers
RESOLUTION_MAP = {
    TEAM1: "p2",  # Oilers win
    TEAM2: "p1",  # Panthers win
    "50-50": "p3",
    "Too early to resolve": "p4",
}

# API Configuration
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-nhl-proxy/GamesByDate/"

# Function to make API requests
def make_request(date):
    url = f"{PRIMARY_ENDPOINT}{date}"
    proxy_url = f"{PROXY_ENDPOINT}{date}"
    try:
        response = requests.get(proxy_url, headers=HEADERS, timeout=10)
        if not response.ok:
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
                home_score = game["HomeTeamScore"]
                away_score = game["AwayTeamScore"]
                if home_score > away_score:
                    winner = game["HomeTeam"]
                else:
                    winner = game["AwayTeam"]
                return RESOLUTION_MAP.get(winner, "Too early to resolve")
            elif game["Status"] in ["Canceled", "Postponed"]:
                return "50-50"
    return "Too early to resolve"

# Main execution block
if __name__ == "__main__":
    games = make_request(DATE)
    if games:
        recommendation = determine_outcome(games)
    else:
        recommendation = "Too early to resolve"
    print(f"recommendation: {recommendation}")