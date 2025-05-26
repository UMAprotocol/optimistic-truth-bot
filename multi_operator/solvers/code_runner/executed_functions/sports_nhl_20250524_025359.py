import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NHL_API_KEY")

# Configuration for API headers
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

# Define the resolution map using team abbreviations
RESOLUTION_MAP = {
    "EDM": "p2",  # Edmonton Oilers
    "DAL": "p1",  # Dallas Stars
    "50-50": "p3",
    "Too early to resolve": "p4",
}

# Function to make API requests
def make_api_request(url, proxy_url=None):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            if proxy_url:
                response = requests.get(proxy_url, headers=HEADERS, timeout=10)
                if response.status_code == 200:
                    return response.json()
    except requests.exceptions.RequestException as e:
        if proxy_url:
            try:
                response = requests.get(proxy_url, headers=HEADERS, timeout=10)
                if response.status_code == 200:
                    return response.json()
            except requests.exceptions.RequestException:
                pass
    return None

# Function to find the game and determine the outcome
def find_game_and_determine_outcome():
    date_str = "2025-05-23"
    teams = {"EDM": "Edmonton Oilers", "DAL": "Dallas Stars"}
    url = f"https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/{date_str}"
    proxy_url = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-nhl-proxy"

    games = make_api_request(url, proxy_url)
    if games:
        for game in games:
            if {game["HomeTeam"], game["AwayTeam"]} == set(teams.keys()):
                if game["Status"] == "Final":
                    home_score = game["HomeTeamScore"]
                    away_score = game["AwayTeamScore"]
                    if home_score > away_score:
                        winner = game["HomeTeam"]
                    else:
                        winner = game["AwayTeam"]
                    return "recommendation: " + RESOLUTION_MAP[winner]
                elif game["Status"] in ["Canceled", "Postponed"]:
                    return "recommendation: p3"
                else:
                    return "recommendation: p4"
    return "recommendation: p4"

# Main execution
if __name__ == "__main__":
    result = find_game_and_determine_outcome()
    print(result)