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
EVENT_URL = "https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/"
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
MATCH_DATE = "2025-06-10"
TEAM1 = "B8"
TEAM2 = "Lynn Vision"
RESOLUTION_MAP = {
    TEAM1: "p2",  # B8
    TEAM2: "p1",  # Lynn Vision
    "50-50": "p3",
    "Too early to resolve": "p4",
}

# Function to fetch games by date
def fetch_games_by_date(date):
    url = f"{EVENT_URL}{date}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    else:
        return None

# Function to determine the outcome of the match
def determine_outcome(games, team1, team2):
    for game in games:
        if {game["HomeTeam"], game["AwayTeam"]} == {team1, team2}:
            if game["Status"] == "Final":
                home_score = game["HomeTeamRuns"]
                away_score = game["AwayTeamRuns"]
                if home_score == away_score:
                    return RESOLUTION_MAP["50-50"]
                elif (home_score > away_score and game["HomeTeam"] == team1) or (away_score > home_score and game["AwayTeam"] == team1):
                    return RESOLUTION_MAP[team1]
                else:
                    return RESOLUTION_MAP[team2]
            elif game["Status"] in ["Canceled", "Postponed"]:
                return RESOLUTION_MAP["50-50"]
            else:
                return RESOLUTION_MAP["Too early to resolve"]
    return RESOLUTION_MAP["Too early to resolve"]

# Main execution block
if __name__ == "__main__":
    games = fetch_games_by_date(MATCH_DATE)
    if games:
        recommendation = determine_outcome(games, TEAM1, TEAM2)
    else:
        recommendation = RESOLUTION_MAP["Too early to resolve"]
    print("recommendation:", recommendation)