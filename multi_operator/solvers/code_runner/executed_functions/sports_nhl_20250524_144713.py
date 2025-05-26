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
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nhl/scores/json"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-nhl-proxy"

# Resolution map based on the ancillary data provided
RESOLUTION_MAP = {
    "SWE": "p2",  # Sweden wins
    "USA": "p1",  # USA wins
    "50-50": "p3"  # Game canceled or postponed beyond the limit
}

# Function to make API requests with a fallback mechanism
def make_api_request(endpoint, path):
    url = f"{endpoint}/{path}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if endpoint == PRIMARY_ENDPOINT:
            print(f"Failed to fetch data from primary endpoint: {e}")
            return None
        else:
            print(f"Failed to fetch data from proxy endpoint, trying primary: {e}")
            return make_api_request(PRIMARY_ENDPOINT, path)

# Function to determine the outcome of the game
def determine_outcome(game_date, team1, team2):
    date_str = game_date.strftime("%Y-%m-%d")
    games_today = make_api_request(PROXY_ENDPOINT, f"GamesByDate/{date_str}")
    if not games_today:
        return "recommendation: p4"

    for game in games_today:
        if {game["HomeTeam"], game["AwayTeam"]} == {team1, team2}:
            if game["Status"] == "Final":
                if game["HomeTeamRuns"] > game["AwayTeamRuns"]:
                    winner = game["HomeTeam"]
                else:
                    winner = game["AwayTeam"]
                return f"recommendation: {RESOLUTION_MAP.get(winner, 'p4')}"
            elif game["Status"] in ["Canceled", "Postponed"]:
                return "recommendation: p3"
            else:
                return "recommendation: p4"

    return "recommendation: p4"

# Main execution function
def main():
    game_date = datetime(2025, 5, 24)
    team1 = "USA"
    team2 = "SWE"
    result = determine_outcome(game_date, team1, team2)
    print(result)

if __name__ == "__main__":
    main()