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
GAME_DATE = "2025-06-10"
HOME_TEAM = "PHI"  # Philadelphia Phillies
AWAY_TEAM = "CHC"  # Chicago Cubs

# Resolution map
RESOLUTION_MAP = {
    HOME_TEAM: "p1",  # Phillies win
    AWAY_TEAM: "p2",  # Cubs win
    "Canceled": "p3",  # Game canceled
    "Postponed": "p4",  # Game postponed
    "Scheduled": "p4"  # Game scheduled/not yet played
}

def get_game_data(date):
    """Fetch game data for a specific date."""
    url = f"{PRIMARY_ENDPOINT}/GamesByDate/{date}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error accessing primary endpoint: {e}")
        try:
            # Fallback to proxy endpoint
            proxy_url = f"{PROXY_ENDPOINT}/GamesByDate/{date}"
            response = requests.get(proxy_url, headers=HEADERS, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error accessing proxy endpoint: {e}")
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
            else:
                return RESOLUTION_MAP.get(game["Status"], "p4")
    return "p4"  # No relevant game found or no final result yet

def main():
    games = get_game_data(GAME_DATE)
    if games:
        recommendation = analyze_game_data(games)
    else:
        recommendation = "p4"  # Unable to retrieve data
    print(f"recommendation: {recommendation}")

if __name__ == "__main__":
    main()