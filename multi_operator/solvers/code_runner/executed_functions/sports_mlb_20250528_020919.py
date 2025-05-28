import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
MLB_API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not MLB_API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# API configuration
HEADERS = {"Ocp-Apim-Subscription-Key": MLB_API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/mlb/scores/json"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/mlb-proxy"

# Game details
GAME_DATE = "2025-05-27"
HOME_TEAM = "Cincinnati Reds"
AWAY_TEAM = "Kansas City Royals"

# Resolution map
RESOLUTION_MAP = {
    HOME_TEAM: "p2",  # Reds win
    AWAY_TEAM: "p1",  # Royals win
    "Canceled": "p3",  # Game canceled
    "Postponed": "p4",  # Game postponed
    "Unknown": "p4"  # Unknown or in-progress
}

def get_game_data(date):
    """Fetch game data for a specific date."""
    url = f"{PRIMARY_ENDPOINT}/GamesByDate/{date}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Primary endpoint failed: {e}, trying proxy...")
        try:
            proxy_url = f"{PROXY_ENDPOINT}/GamesByDate/{date}"
            response = requests.get(proxy_url, headers=HEADERS, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Proxy endpoint also failed: {e}")
            return None

def analyze_game_data(games):
    """Analyze game data to determine the outcome."""
    for game in games:
        if {game["HomeTeam"], game["AwayTeam"]} == {HOME_TEAM, AWAY_TEAM}:
            if game["Status"] == "Final":
                if game["HomeTeamRuns"] > game["AwayTeamRuns"]:
                    return RESOLUTION_MAP[game["HomeTeam"]]
                elif game["AwayTeamRuns"] > game["HomeTeamRuns"]:
                    return RESOLUTION_MAP[game["AwayTeam"]]
            elif game["Status"] in ["Canceled", "Postponed"]:
                return RESOLUTION_MAP[game["Status"]]
    return RESOLUTION_MAP["Unknown"]

def main():
    games = get_game_data(GAME_DATE)
    if games:
        result = analyze_game_data(games)
        print(f"recommendation: {result}")
    else:
        print("recommendation: p4")  # Unable to retrieve data

if __name__ == "__main__":
    main()