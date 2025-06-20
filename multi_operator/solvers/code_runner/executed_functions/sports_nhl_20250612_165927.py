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
DATE = "2025-06-12"
TEAM1 = "G2"  # Use the appropriate NHL abbreviation if applicable
TEAM2 = "3DMAX"  # Use the appropriate NHL abbreviation if applicable
RESOLUTION_MAP = {
    "G2": "p2",  # G2 wins
    "3DMAX": "p1",  # 3DMAX wins
    "50-50": "p3",  # Tie or canceled
    "Too early to resolve": "p4",  # In-progress or no data
}

# API Configuration
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
BASE_URL = "https://api.sportsdata.io/v3/nhl/scores/json"

# Function to fetch games by date
def fetch_games_by_date(date):
    url = f"{BASE_URL}/GamesByDate/{date}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    else:
        return None

# Main function to determine the outcome
def determine_outcome():
    games = fetch_games_by_date(DATE)
    if not games:
        return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

    for game in games:
        if {game["HomeTeam"], game["AwayTeam"]} == {TEAM1, TEAM2}:
            if game["Status"] == "Final":
                if game["HomeTeam"] == TEAM1 and game["HomeTeamScore"] > game["AwayTeamScore"]:
                    return "recommendation: " + RESOLUTION_MAP[TEAM1]
                elif game["AwayTeam"] == TEAM1 and game["AwayTeamScore"] > game["HomeTeamScore"]:
                    return "recommendation: " + RESOLUTION_MAP[TEAM1]
                elif game["HomeTeam"] == TEAM2 and game["HomeTeamScore"] > game["AwayTeamScore"]:
                    return "recommendation: " + RESOLUTION_MAP[TEAM2]
                elif game["AwayTeam"] == TEAM2 and game["AwayTeamScore"] > game["HomeTeamScore"]:
                    return "recommendation: " + RESOLUTION_MAP[TEAM2]
                else:
                    return "recommendation: " + RESOLUTION_MAP["50-50"]
            elif game["Status"] in ["Canceled", "Postponed"]:
                return "recommendation: " + RESOLUTION_MAP["50-50"]
            else:
                return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]
    return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

# Execute the main function
if __name__ == "__main__":
    result = determine_outcome()
    print(result)