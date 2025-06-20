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

# Helper function to make API requests
def make_request(url, headers):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

# Function to find and resolve the game outcome
def resolve_game(date, team1, team2):
    formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = f"https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/{formatted_date}"
    games = make_request(url, HEADERS)
    
    if games is None:
        return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]
    
    for game in games:
        if {game["HomeTeam"], game["AwayTeam"]} == {team1, team2}:
            if game["Status"] == "Final":
                if game["HomeTeam"] == team1 and game["HomeTeamScore"] > game["AwayTeamScore"]:
                    return "recommendation: " + RESOLUTION_MAP[team1]
                elif game["AwayTeam"] == team1 and game["AwayTeamScore"] > game["HomeTeamScore"]:
                    return "recommendation: " + RESOLUTION_MAP[team1]
                elif game["HomeTeam"] == team2 and game["HomeTeamScore"] > game["AwayTeamScore"]:
                    return "recommendation: " + RESOLUTION_MAP[team2]
                elif game["AwayTeam"] == team2 and game["AwayTeamScore"] > game["HomeTeamScore"]:
                    return "recommendation: " + RESOLUTION_MAP[team2]
            elif game["Status"] == "Postponed":
                return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]
            elif game["Status"] == "Canceled":
                return "recommendation: " + RESOLUTION_MAP["50-50"]
    return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

# Main execution
if __name__ == "__main__":
    result = resolve_game(DATE, TEAM1, TEAM2)
    print(result)