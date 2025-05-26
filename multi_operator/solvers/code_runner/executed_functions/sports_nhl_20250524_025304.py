import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NHL_API_KEY")

# Constants
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
DATE = "2025-05-23"
TEAM1 = "EDM"  # Edmonton Oilers
TEAM2 = "DAL"  # Dallas Stars
RESOLUTION_MAP = {
    TEAM1: "p2",  # Oilers win
    TEAM2: "p1",  # Stars win
    "50-50": "p3",
    "Too early to resolve": "p4",
}

# Helper functions
def get_data(url, proxy_url=None):
    try:
        response = requests.get(proxy_url if proxy_url else url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if proxy_url:
            # Try primary endpoint if proxy fails
            return get_data(url)
        else:
            print(f"Error: {e}")
            return None

def find_game(games, team1, team2):
    for game in games:
        if {game["HomeTeam"], game["AwayTeam"]} == {team1, team2}:
            return game
    return None

def resolve_market(game):
    if not game:
        return RESOLUTION_MAP["Too early to resolve"]
    if game["Status"] == "Final":
        if game["HomeTeamRuns"] > game["AwayTeamRuns"]:
            winner = game["HomeTeam"]
        else:
            winner = game["AwayTeam"]
        return RESOLUTION_MAP[winner]
    elif game["Status"] in ["Canceled", "Postponed"]:
        return RESOLUTION_MAP["50-50"]
    else:
        return RESOLUTION_MAP["Too early to resolve"]

# Main execution
def main():
    url = f"https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/{DATE}"
    proxy_url = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-nhl-proxy"
    games = get_data(url, proxy_url)
    if games:
        game = find_game(games, TEAM1, TEAM2)
        result = resolve_market(game)
        print(f"recommendation: {result}")
    else:
        print("recommendation: p4")

if __name__ == "__main__":
    main()