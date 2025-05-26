import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NHL_API_KEY")

# Configuration for API requests
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nhl"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/nhl-proxy"

# Resolution map based on the ancillary data provided
RESOLUTION_MAP = {
    "DC": "p2",  # Delhi Capitals
    "PB": "p1",  # Punjab Kings
    "50-50": "p3",
    "Too early to resolve": "p4",
}

# Function to make API requests
def make_request(url, use_proxy=False):
    endpoint = PROXY_ENDPOINT if use_proxy else PRIMARY_ENDPOINT
    full_url = f"{endpoint}{url}"
    try:
        response = requests.get(full_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if use_proxy:
            print("Proxy failed, trying primary endpoint.")
            return make_request(url, use_proxy=False)
        else:
            print(f"Failed to retrieve data: {e}")
            return None

# Function to determine the outcome of the match
def determine_outcome(game_date, team1, team2):
    formatted_date = datetime.strptime(game_date, "%Y-%m-%d").strftime("%Y-%m-%d")
    games = make_request(f"/scores/json/GamesByDate/{formatted_date}", use_proxy=True)
    if games:
        for game in games:
            if {game["HomeTeam"], game["AwayTeam"]} == {team1, team2}:
                if game["Status"] == "Final":
                    if game["HomeTeam"] == team1 and game["HomeTeamRuns"] > game["AwayTeamRuns"]:
                        return RESOLUTION_MAP[team1]
                    elif game["AwayTeam"] == team1 and game["AwayTeamRuns"] > game["HomeTeamRuns"]:
                        return RESOLUTION_MAP[team1]
                    elif game["HomeTeam"] == team2 and game["HomeTeamRuns"] > game["AwayTeamRuns"]:
                        return RESOLUTION_MAP[team2]
                    elif game["AwayTeam"] == team2 and game["AwayTeamRuns"] > game["HomeTeamRuns"]:
                        return RESOLUTION_MAP[team2]
                elif game["Status"] in ["Canceled", "Postponed"]:
                    return RESOLUTION_MAP["50-50"]
    return RESOLUTION_MAP["Too early to resolve"]

# Main function to run the program
if __name__ == "__main__":
    game_date = "2025-05-24"
    team1 = "DC"  # Delhi Capitals
    team2 = "PB"  # Punjab Kings
    result = determine_outcome(game_date, team1, team2)
    print(f"recommendation: {result}")