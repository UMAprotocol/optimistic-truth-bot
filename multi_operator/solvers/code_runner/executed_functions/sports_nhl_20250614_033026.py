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
GAME_DATE = "2025-06-13"
TEAM1 = "OKC"  # Oklahoma City Thunder
TEAM2 = "IND"  # Indiana Pacers

# Resolution map based on the outcome
RESOLUTION_MAP = {
    TEAM1: "p2",  # Thunder win
    TEAM2: "p1",  # Pacers win
    "Postponed": "p4",  # Game postponed
    "Canceled": "p3",  # Game canceled
    "Unknown": "p4"  # Unknown or in-progress
}

def get_game_data(date):
    """Fetch game data for a specific date."""
    url = f"{PRIMARY_ENDPOINT}/scores/json/GamesByDate/{date}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from primary endpoint: {e}")
        try:
            # Fallback to proxy endpoint
            response = requests.get(PROXY_ENDPOINT, headers=HEADERS, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data from proxy endpoint: {e}")
            return None

def analyze_game_data(games):
    """Analyze game data to determine the outcome."""
    for game in games:
        if {game["HomeTeam"], game["AwayTeam"]} == {TEAM1, TEAM2}:
            if game["Status"] == "Final":
                if game["HomeTeam"] == TEAM1 and game["HomeTeamScore"] > game["AwayTeamScore"]:
                    return RESOLUTION_MAP[TEAM1]
                elif game["AwayTeam"] == TEAM1 and game["AwayTeamScore"] > game["HomeTeamScore"]:
                    return RESOLUTION_MAP[TEAM1]
                else:
                    return RESOLUTION_MAP[TEAM2]
            elif game["Status"] == "Postponed":
                return RESOLUTION_MAP["Postponed"]
            elif game["Status"] == "Canceled":
                return RESOLUTION_MAP["Canceled"]
    return RESOLUTION_MAP["Unknown"]

if __name__ == "__main__":
    games = get_game_data(GAME_DATE)
    if games:
        recommendation = analyze_game_data(games)
    else:
        recommendation = RESOLUTION_MAP["Unknown"]
    print(f"recommendation: {recommendation}")