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
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-proxy/nba"

# Game details
GAME_DATE = "2025-05-29"
TEAM1_ABBR = "IND"  # Indiana Pacers
TEAM2_ABBR = "NY"   # New York Knicks

# Resolution map based on the outcome
RESOLUTION_MAP = {
    TEAM1_ABBR: "p2",  # Pacers win
    TEAM2_ABBR: "p1",  # Knicks win
    "Postponed": "p4",  # Game postponed
    "Canceled": "p3",   # Game canceled
    "Unknown": "p4"     # Unknown or in-progress
}

def get_game_data(date):
    """Fetch game data for a specific date."""
    url = f"{PROXY_ENDPOINT}/scores/json/GamesByDate/{date}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if not response.ok:
            # Fallback to primary endpoint if proxy fails
            url = f"{PRIMARY_ENDPOINT}/scores/json/GamesByDate/{date}"
            response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching game data: {e}")
        return None

def analyze_game_outcome(games):
    """Determine the outcome of the game based on the fetched data."""
    for game in games:
        if {game["HomeTeam"], game["AwayTeam"]} == {TEAM1_ABBR, TEAM2_ABBR}:
            if game["Status"] == "Final":
                if game["HomeTeam"] == TEAM1_ABBR and game["HomeTeamScore"] > game["AwayTeamScore"]:
                    return RESOLUTION_MAP[TEAM1_ABBR]
                elif game["AwayTeam"] == TEAM1_ABBR and game["AwayTeamScore"] > game["HomeTeamScore"]:
                    return RESOLUTION_MAP[TEAM1_ABBR]
                else:
                    return RESOLUTION_MAP[TEAM2_ABBR]
            else:
                return RESOLUTION_MAP.get(game["Status"], "Unknown")
    return "Unknown"

if __name__ == "__main__":
    games = get_game_data(GAME_DATE)
    if games:
        recommendation = analyze_game_outcome(games)
    else:
        recommendation = "Unknown"
    print(f"recommendation: {RESOLUTION_MAP.get(recommendation, 'p4')}")