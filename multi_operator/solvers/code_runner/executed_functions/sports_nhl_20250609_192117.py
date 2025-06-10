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
RESOLUTION_MAP = {
    "FLA": "p2",  # Florida Panthers
    "CAR": "p1",  # Carolina Hurricanes
    "50-50": "p3",
    "Too early to resolve": "p4",
}

# Helper functions
def get_game_data(date):
    url = f"https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/{date}"
    response = requests.get(url, headers=HEADERS, timeout=10)
    if response.status_code == 200:
        return response.json()
    return None

def analyze_game_results(games, team1, team2):
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
            elif game["Status"] == "Postponed":
                return RESOLUTION_MAP["Too early to resolve"]
            elif game["Status"] == "Canceled":
                return RESOLUTION_MAP["50-50"]
    return RESOLUTION_MAP["Too early to resolve"]

# Main execution
if __name__ == "__main__":
    game_date = "2025-05-28"
    team1 = "CAR"  # Carolina Hurricanes
    team2 = "FLA"  # Florida Panthers

    games = get_game_data(game_date)
    if games:
        recommendation = analyze_game_results(games, team1, team2)
    else:
        recommendation = RESOLUTION_MAP["Too early to resolve"]

    print("recommendation:", recommendation)