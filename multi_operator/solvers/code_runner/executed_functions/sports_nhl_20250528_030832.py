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
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nba/scores/json/GamesByDate/"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-proxy/nba/GamesByDate/"

# Resolution map based on the ancillary data provided
RESOLUTION_MAP = {
    "NYK": "p2",  # New York Knicks
    "IND": "p1",  # Indiana Pacers
    "Postponed": "p4",
    "Canceled": "p3"
}

def get_game_data(date):
    # Try proxy endpoint first
    try:
        response = requests.get(f"{PROXY_ENDPOINT}{date}", headers=HEADERS, timeout=10)
        if response.status_code == 200:
            return response.json()
    except requests.RequestException:
        pass

    # Fallback to primary endpoint
    try:
        response = requests.get(f"{PRIMARY_ENDPOINT}{date}", headers=HEADERS, timeout=10)
        if response.status_code == 200:
            return response.json()
    except requests.RequestException as e:
        print(f"Failed to retrieve data: {str(e)}")
        return None

def analyze_game_results(games):
    for game in games:
        if {"NYK", "IND"}.issubset({game["HomeTeam"], game["AwayTeam"]}):
            if game["Status"] == "Final":
                home_team = game["HomeTeam"]
                away_team = game["AwayTeam"]
                home_score = game["HomeTeamScore"]
                away_score = game["AwayTeamScore"]
                if home_score > away_score:
                    winner = home_team
                else:
                    winner = away_team
                return RESOLUTION_MAP.get(winner, "p4")
            elif game["Status"] in ["Postponed", "Canceled"]:
                return RESOLUTION_MAP[game["Status"]]
    return "p4"

def main():
    # Game date from the user prompt
    game_date = "2025-05-27"
    games = get_game_data(game_date)
    if games:
        recommendation = analyze_game_results(games)
    else:
        recommendation = "p4"
    print(f"recommendation: {recommendation}")

if __name__ == "__main__":
    main()