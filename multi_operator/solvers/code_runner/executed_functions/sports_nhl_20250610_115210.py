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
DATE = "2025-06-09"
TEAM1 = "EDM"  # Edmonton Oilers
TEAM2 = "FLA"  # Florida Panthers
RESOLUTION_MAP = {
    TEAM1: "p2",  # Oilers win
    TEAM2: "p1",  # Panthers win
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

def find_game(date, team1, team2):
    formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = f"https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/{formatted_date}"
    proxy_url = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-nhl-proxy"
    games = get_data(url, proxy_url)
    if games:
        for game in games:
            if {game["HomeTeam"], game["AwayTeam"]} == {team1, team2}:
                return game
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

# Main execution
if __name__ == "__main__":
    game = find_game(DATE, TEAM1, TEAM2)
    result = resolve_market(game)
    print(result)