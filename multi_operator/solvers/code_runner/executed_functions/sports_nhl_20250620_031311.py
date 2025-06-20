import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NBA_API_KEY")

# Constants
DATE = "2025-06-19"
TEAM1 = "OKC"  # Oklahoma City Thunder
TEAM2 = "IND"  # Indiana Pacers
RESOLUTION_MAP = {
    TEAM1: "p2",  # Thunder win
    TEAM2: "p1",  # Pacers win
    "50-50": "p3",
    "Too early to resolve": "p4",
}

# API Configuration
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nba/scores/json/GamesByDate/"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/nba-proxy/GamesByDate/"

# Function to fetch data from API
def fetch_data(date):
    url = f"{PRIMARY_ENDPOINT}{date}"
    proxy_url = f"{PROXY_ENDPOINT}{date}"
    try:
        response = requests.get(proxy_url, headers=HEADERS, timeout=10)
        if not response.ok:
            raise Exception("Proxy failed")
        return response.json()
    except:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.ok:
            return response.json()
        response.raise_for_status()

# Determine the outcome based on the fetched data
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
                return RESOLUTION_MAP.get(winner, "p4")
            elif game["Status"] in ["Postponed", "Canceled"]:
                return "p3"
            else:
                return "p4"
    return "p4"

# Main execution
if __name__ == "__main__":
    games = fetch_data(DATE)
    result = determine_outcome(games)
    print("recommendation:", result)