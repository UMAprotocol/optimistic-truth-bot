import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NHL_API_KEY")
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

# Constants
GAME_DATE = "2025-06-12"
TEAM1 = "FLA"  # Florida Panthers
TEAM2 = "EDM"  # Edmonton Oilers
RESOLUTION_MAP = {
    "No": "p1",
    "Yes": "p2",
    "50-50": "p3"
}

# Function to get game data
def get_game_data(date):
    url = f"https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/{date}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        games = response.json()
        for game in games:
            if {game["HomeTeam"], game["AwayTeam"]} == {TEAM1, TEAM2}:
                return game
    return None

# Main function to determine the outcome
def resolve_market():
    game = get_game_data(GAME_DATE)
    if not game:
        return "recommendation: " + RESOLUTION_MAP["50-50"]
    if game["Status"] == "Final":
        if game["IsOvertime"]:
            return "recommendation: " + RESOLUTION_MAP["Yes"]
        else:
            return "recommendation: " + RESOLUTION_MAP["No"]
    elif game["Status"] in ["Canceled", "Postponed"]:
        return "recommendation: " + RESOLUTION_MAP["50-50"]
    else:
        return "recommendation: " + RESOLUTION_MAP["50-50"]

# Execute the main function
if __name__ == "__main__":
    print(resolve_market())