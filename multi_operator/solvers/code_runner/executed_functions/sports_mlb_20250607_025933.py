import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# Configuration for headers and API endpoints
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/mlb/scores/json"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/mlb-proxy"

# Resolution map based on the game outcome
RESOLUTION_MAP = {
    "Blue Jays": "p2",
    "Twins": "p1",
    "50-50": "p3",
    "Too early to resolve": "p4"
}

# Function to make API requests
def make_api_request(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

# Function to find and resolve the game outcome
def resolve_game(date_str, team1, team2):
    formatted_date = datetime.strptime(date_str, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = f"{PRIMARY_ENDPOINT}/GamesByDate/{formatted_date}"
    games = make_api_request(url)
    if games is None:
        print("Failed to retrieve data from primary endpoint, trying proxy...")
        url = f"{PROXY_ENDPOINT}/GamesByDate/{formatted_date}"
        games = make_api_request(url)
        if games is None:
            return "recommendation: p4"  # Unable to resolve due to API failure

    for game in games:
        if (game["HomeTeam"] == team1 and game["AwayTeam"] == team2) or (game["HomeTeam"] == team2 and game["AwayTeam"] == team1):
            if game["Status"] == "Final":
                home_team_wins = game["HomeTeamRuns"] > game["AwayTeamRuns"]
                if home_team_wins:
                    return "recommendation: " + RESOLUTION_MAP[game["HomeTeam"]]
                else:
                    return "recommendation: " + RESOLUTION_MAP[game["AwayTeam"]]
            elif game["Status"] == "Canceled":
                return "recommendation: p3"
            elif game["Status"] == "Postponed":
                return "recommendation: p4"
    return "recommendation: p4"

# Main execution function
if __name__ == "__main__":
    game_date = "2025-06-06"
    team1 = "MIN"  # Minnesota Twins
    team2 = "TOR"  # Toronto Blue Jays
    print(resolve_game(game_date, team1, team2))