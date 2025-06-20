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
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nhl/scores/json"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/nhl-proxy"
HEADERS = {"Ocp-Apim-Subscription-Key": NHL_API_KEY}
RESOLUTION_MAP = {
    "EDM": "p2",  # Oilers
    "FLA": "p1",  # Panthers
    "50-50": "p3",
    "Too early to resolve": "p4",
}

# Helper function to make API requests
def make_request(endpoint, path):
    try:
        response = requests.get(f"{endpoint}{path}", headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        return None

# Main function to determine the outcome of the game
def resolve_nhl_game(date_str, team1, team2):
    # Format the date for the API request
    game_date = datetime.strptime(date_str, "%Y-%m-%d").strftime("%Y-%m-%d")
    path = f"/GamesByDate/{game_date}"

    # Try proxy endpoint first
    games = make_request(PROXY_ENDPOINT, path)
    if games is None:
        # Fallback to primary endpoint if proxy fails
        games = make_request(PRIMARY_ENDPOINT, path)
        if games is None:
            return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

    # Analyze the game data
    for game in games:
        if {game["HomeTeam"], game["AwayTeam"]} == {team1, team2}:
            if game["Status"] == "Final":
                if game["HomeTeam"] == team1 and game["HomeTeamRuns"] > game["AwayTeamRuns"]:
                    return "recommendation: " + RESOLUTION_MAP[team1]
                elif game["AwayTeam"] == team1 and game["AwayTeamRuns"] > game["HomeTeamRuns"]:
                    return "recommendation: " + RESOLUTION_MAP[team1]
                else:
                    return "recommendation: " + RESOLUTION_MAP[team2]
            elif game["Status"] in ["Canceled", "Postponed"]:
                return "recommendation: " + RESOLUTION_MAP["50-50"]
            else:
                return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

    return "recommendation: " + RESOLUTION_MAP["Too early to resolve"]

# Execute the function with the specific game details
if __name__ == "__main__":
    result = resolve_nhl_game("2025-06-12", "EDM", "FLA")
    print(result)