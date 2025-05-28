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

# Game details
GAME_DATE = "2025-05-26"
TEAM1 = "OKC"  # Oklahoma City Thunder
TEAM2 = "MIN"  # Minnesota Timberwolves

# Resolution map based on the outcome
RESOLUTION_MAP = {
    TEAM1: "p2",  # Thunder win
    TEAM2: "p1",  # Timberwolves win
    "Postponed": "p4",  # Game postponed
    "Canceled": "p3",  # Game canceled
    "Unknown": "p4"  # Unknown or in-progress
}

def get_game_data(date, team1, team2):
    # Try proxy endpoint first
    url = f"{PROXY_ENDPOINT}/scores/json/GamesByDate/{date}"
    response = requests.get(url, headers=HEADERS, timeout=10)
    if not response.ok:
        # Fallback to primary endpoint
        url = f"{PRIMARY_ENDPOINT}/scores/json/GamesByDate/{date}"
        response = requests.get(url, headers=HEADERS, timeout=10)
    if response.ok:
        games = response.json()
        for game in games:
            if {game["HomeTeam"], game["AwayTeam"]} == {team1, team2}:
                return game
    return None

def resolve_market(game):
    if not game:
        return "recommendation: " + RESOLUTION_MAP["Unknown"]
    if game["Status"] == "Final":
        if game["HomeTeamRuns"] > game["AwayTeamRuns"]:
            winner = game["HomeTeam"]
        else:
            winner = game["AwayTeam"]
        return "recommendation: " + RESOLUTION_MAP[winner]
    elif game["Status"] in ["Postponed", "Canceled"]:
        return "recommendation: " + RESOLUTION_MAP[game["Status"]]
    else:
        return "recommendation: " + RESOLUTION_MAP["Unknown"]

if __name__ == "__main__":
    game_info = get_game_data(GAME_DATE, TEAM1, TEAM2)
    result = resolve_market(game_info)
    print(result)