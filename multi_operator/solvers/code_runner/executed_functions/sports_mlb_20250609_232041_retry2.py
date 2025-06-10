import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# Configuration for API requests
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/mlb/scores/json"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/mlb-proxy"

# Resolution map based on the game outcome
RESOLUTION_MAP = {
    "Angels": "p2",
    "Guardians": "p1",
    "50-50": "p3",
    "Too early to resolve": "p4"
}

# Function to make API requests
def make_api_request(url, use_proxy=False):
    endpoint = PROXY_ENDPOINT if use_proxy else PRIMARY_ENDPOINT
    full_url = f"{endpoint}{url}"
    try:
        response = requests.get(full_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if use_proxy:
            print("Proxy failed, trying primary endpoint.")
            return make_api_request(url, use_proxy=False)
        else:
            print(f"API request failed: {e}")
            return None

# Function to determine the outcome of the game
def determine_outcome(game_date, home_team, away_team):
    formatted_date = datetime.strptime(game_date, "%Y-%m-%d").strftime("%Y-%m-%d")
    games = make_api_request(f"/GamesByDate/{formatted_date}", use_proxy=True)
    if games:
        for game in games:
            if game['HomeTeam'] == home_team and game['AwayTeam'] == away_team:
                if game['Status'] == "Final":
                    home_score = game['HomeTeamRuns']
                    away_score = game['AwayTeamRuns']
                    if home_score > away_score:
                        return RESOLUTION_MAP[home_team]
                    elif away_score > home_score:
                        return RESOLUTION_MAP[away_team]
                elif game['Status'] in ["Canceled", "Postponed"]:
                    return RESOLUTION_MAP["50-50"]
                else:
                    return RESOLUTION_MAP["Too early to resolve"]
    return RESOLUTION_MAP["Too early to resolve"]

# Main function to run the resolver
def main():
    game_date = "2025-05-30"
    home_team = "Guardians"
    away_team = "Angels"
    result = determine_outcome(game_date, home_team, away_team)
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()