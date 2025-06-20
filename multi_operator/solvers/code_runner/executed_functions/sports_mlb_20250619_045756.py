import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# Configuration for headers and endpoints
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/mlb/scores/json"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/mlb-proxy"

# Function to handle API requests with fallback mechanism
def get_api_data(url, proxy=False):
    endpoint = PROXY_ENDPOINT if proxy else PRIMARY_ENDPOINT
    full_url = f"{endpoint}{url}"
    try:
        response = requests.get(full_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if proxy:
            # Fallback to primary endpoint if proxy fails
            return get_api_data(url, proxy=False)
        else:
            print(f"API request failed: {e}")
            return None

# Function to determine the outcome of the game
def resolve_market(date, team1, team2):
    games_today = get_api_data(f"/GamesByDate/{date}")
    if games_today is None:
        return "recommendation: p4"  # Unable to retrieve data

    for game in games_today:
        if {game["HomeTeam"], game["AwayTeam"]} == {team1, team2}:
            if game["Status"] == "Final":
                if game["HomeTeamRuns"] > game["AwayTeamRuns"]:
                    winner = game["HomeTeam"]
                else:
                    winner = game["AwayTeam"]
                
                if winner == team1:
                    return "recommendation: p1"
                elif winner == team2:
                    return "recommendation: p2"
            elif game["Status"] in ["Canceled", "Postponed"]:
                return "recommendation: p3"
            else:
                return "recommendation: p4"  # Game not final or other status

    return "recommendation: p4"  # No matching game found

# Main execution
if __name__ == "__main__":
    # Define the game date and teams
    game_date = "2025-06-18"
    team1 = "HOU"  # Houston Astros
    team2 = "OAK"  # Oakland Athletics

    # Resolve the market based on the game outcome
    result = resolve_market(game_date, team1, team2)
    print(result)