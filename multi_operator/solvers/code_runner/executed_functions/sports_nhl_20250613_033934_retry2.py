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
    "EDM": "p2",  # Edmonton Oilers
    "FLA": "p1",  # Florida Panthers
    "50-50": "p3",
    "Too early to resolve": "p4",
}

# Helper functions
def get_game_data(date, team1, team2):
    url = f"{PRIMARY_ENDPOINT}/GamesByDate/{date}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        games = response.json()
        for game in games:
            if (game["HomeTeam"] == team1 and game["AwayTeam"] == team2) or \
               (game["HomeTeam"] == team2 and game["AwayTeam"] == team1):
                return game
    except requests.RequestException:
        try:
            # Fallback to proxy endpoint
            response = requests.get(f"{PROXY_ENDPOINT}/GamesByDate/{date}", headers=HEADERS, timeout=10)
            response.raise_for_status()
            games = response.json()
            for game in games:
                if (game["HomeTeam"] == team1 and game["AwayTeam"] == team2) or \
                   (game["HomeTeam"] == team2 and game["AwayTeam"] == team1):
                    return game
        except requests.RequestException:
            pass
    return None

def resolve_market(game):
    if not game:
        return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]
    if game["Status"] == "Final":
        if game["HomeTeamRuns"] > game["AwayTeamRuns"]:
            winner = game["HomeTeam"]
        else:
            winner = game["AwayTeam"]
        return "recommendation: " + RESOLUTION_MAP.get(winner, "p3")
    elif game["Status"] in ["Canceled", "Postponed"]:
        return "recommendation: " + RESOLUTION_MAP["50-50"]
    else:
        return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

# Main execution
if __name__ == "__main__":
    game_date = "2025-06-12"
    team1 = "EDM"
    team2 = "FLA"
    game_info = get_game_data(game_date, team1, team2)
    result = resolve_market(game_info)
    print(result)