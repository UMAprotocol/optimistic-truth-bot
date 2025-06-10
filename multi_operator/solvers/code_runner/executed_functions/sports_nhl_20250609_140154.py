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
DATE = "2025-05-28"
TEAM1 = "MIN"  # Minnesota Timberwolves
TEAM2 = "OKC"  # Oklahoma City Thunder
RESOLUTION_MAP = {
    TEAM1: "p2",  # Timberwolves win
    TEAM2: "p1",  # Thunder win
    "50-50": "p3",
    "Too early to resolve": "p4",
}

# API Configuration
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nba/scores/json/GamesByDate/"
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

def get_game_data(date):
    url = f"{PRIMARY_ENDPOINT}{date}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        games = response.json()
        for game in games:
            if {game["HomeTeam"], game["AwayTeam"]} == {TEAM1, TEAM2}:
                return game
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
    return None

def resolve_market(game):
    if not game:
        return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]
    if game["Status"] == "Final":
        if game["HomeTeam"] == TEAM1 and game["HomeTeamScore"] > game["AwayTeamScore"]:
            return "recommendation: " + RESOLUTION_MAP[TEAM1]
        elif game["AwayTeam"] == TEAM1 and game["AwayTeamScore"] > game["HomeTeamScore"]:
            return "recommendation: " + RESOLUTION_MAP[TEAM1]
        elif game["HomeTeam"] == TEAM2 and game["HomeTeamScore"] > game["AwayTeamScore"]:
            return "recommendation: " + RESOLUTION_MAP[TEAM2]
        elif game["AwayTeam"] == TEAM2 and game["AwayTeamScore"] > game["HomeTeamScore"]:
            return "recommendation: " + RESOLUTION_MAP[TEAM2]
    elif game["Status"] in ["Canceled", "Postponed"]:
        return "recommendation: " + RESOLUTION_MAP["50-50"]
    return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

if __name__ == "__main__":
    game_info = get_game_data(DATE)
    result = resolve_market(game_info)
    print(result)