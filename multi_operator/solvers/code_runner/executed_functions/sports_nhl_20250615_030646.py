import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NHL_API_KEY")

# Configuration
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nhl/scores/json"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-nhl-proxy"

# Resolution map based on the ancillary data provided
RESOLUTION_MAP = {
    "FLA": "p2",  # Florida Panthers
    "EDM": "p1",  # Edmonton Oilers
    "50-50": "p3",
    "Too early to resolve": "p4",
}

# Helper functions
def get_game_data(date):
    url = f"{PRIMARY_ENDPOINT}/GamesByDate/{date}"
    proxy_url = f"{PROXY_ENDPOINT}/GamesByDate/{date}"
    try:
        response = requests.get(proxy_url, headers=HEADERS, timeout=10)
        if not response.ok:
            raise Exception("Proxy failed")
    except Exception:
        response = requests.get(url, headers=HEADERS, timeout=10)
    if response.ok:
        return response.json()
    return None

def analyze_game_data(games, team1, team2):
    for game in games:
        if {game["HomeTeam"], game["AwayTeam"]} == {team1, team2}:
            if game["Status"] == "Final":
                if game["HomeTeam"] == team1 and game["HomeTeamRuns"] > game["AwayTeamRuns"]:
                    return RESOLUTION_MAP[team1]
                elif game["AwayTeam"] == team1 and game["AwayTeamRuns"] > game["HomeTeamRuns"]:
                    return RESOLUTION_MAP[team1]
                else:
                    return RESOLUTION_MAP[team2]
            elif game["Status"] in ["Canceled", "Postponed"]:
                return RESOLUTION_MAP["50-50"]
            else:
                return RESOLUTION_MAP["Too early to resolve"]
    return RESOLUTION_MAP["Too early to resolve"]

# Main execution
if __name__ == "__main__":
    game_date = "2025-06-14"
    team1 = "EDM"  # Edmonton Oilers
    team2 = "FLA"  # Florida Panthers

    games = get_game_data(game_date)
    if games:
        recommendation = analyze_game_data(games, team1, team2)
    else:
        recommendation = RESOLUTION_MAP["Too early to resolve"]

    print(f"recommendation: {recommendation}")