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
DATE = "2025-06-14"
TEAM1 = "MongolZ"  # Example abbreviation, replace with actual if different
TEAM2 = "FaZe"     # Example abbreviation, replace with actual if different
RESOLUTION_MAP = {
    TEAM1: "p2",  # MongolZ win
    TEAM2: "p1",  # FaZe win
    "50-50": "p3",
    "Too early to resolve": "p4",
}

# Function to get game data
def get_game_data(date):
    url = f"https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/{date}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    else:
        return None

# Function to determine the outcome
def determine_outcome(games, team1, team2):
    for game in games:
        if {game['HomeTeam'], game['AwayTeam']} == {team1, team2}:
            if game['Status'] == "Final":
                if game['HomeTeamRuns'] > game['AwayTeamRuns']:
                    winner = game['HomeTeam']
                else:
                    winner = game['AwayTeam']
                return RESOLUTION_MAP.get(winner, "p4")
            elif game['Status'] in ["Canceled", "Postponed"]:
                return RESOLUTION_MAP["50-50"]
            else:
                return RESOLUTION_MAP["Too early to resolve"]
    return RESOLUTION_MAP["Too early to resolve"]

# Main execution
if __name__ == "__main__":
    games = get_game_data(DATE)
    if games:
        recommendation = determine_outcome(games, TEAM1, TEAM2)
    else:
        recommendation = RESOLUTION_MAP["Too early to resolve"]
    print("recommendation:", recommendation)