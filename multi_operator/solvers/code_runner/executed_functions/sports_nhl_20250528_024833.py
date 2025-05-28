import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
NHL_API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
if not NHL_API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NHL_API_KEY")

# Constants
HEADERS = {"Ocp-Apim-Subscription-Key": NHL_API_KEY}
DATE = "2025-05-27"
TEAM1 = "DAL"  # Dallas Stars
TEAM2 = "EDM"  # Edmonton Oilers
RESOLUTION_MAP = {
    TEAM1: "p2",  # Dallas Stars win
    TEAM2: "p1",  # Edmonton Oilers win
    "50-50": "p3",  # Game canceled
    "Too early to resolve": "p4",  # Game not yet played or in progress
}

# Helper functions
def get_nhl_data(date):
    url = f"https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/{date}"
    response = requests.get(url, headers=HEADERS, timeout=10)
    if response.status_code == 200:
        return response.json()
    else:
        response.raise_for_status()

def resolve_market(games, team1, team2):
    for game in games:
        if {game["HomeTeam"], game["AwayTeam"]} == {team1, team2}:
            if game["Status"] == "Final":
                if game["HomeTeam"] == team1 and game["HomeTeamScore"] > game["AwayTeamScore"]:
                    return RESOLUTION_MAP[team1]
                elif game["AwayTeam"] == team1 and game["AwayTeamScore"] > game["HomeTeamScore"]:
                    return RESOLUTION_MAP[team1]
                elif game["HomeTeam"] == team2 and game["HomeTeamScore"] > game["AwayTeamScore"]:
                    return RESOLUTION_MAP[team2]
                elif game["AwayTeam"] == team2 and game["AwayTeamScore"] > game["HomeTeamScore"]:
                    return RESOLUTION_MAP[team2]
            elif game["Status"] == "Canceled":
                return RESOLUTION_MAP["50-50"]
            elif game["Status"] == "Postponed":
                return RESOLUTION_MAP["Too early to resolve"]
    return RESOLUTION_MAP["Too early to resolve"]

# Main execution
if __name__ == "__main__":
    try:
        games = get_nhl_data(DATE)
        recommendation = resolve_market(games, TEAM1, TEAM2)
        print("recommendation:", recommendation)
    except Exception as e:
        print("Error:", str(e))