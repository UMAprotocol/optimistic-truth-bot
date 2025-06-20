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
            print(f"Proxy failed, trying primary endpoint. Error: {e}")
            return get_api_data(url, proxy=False)
        else:
            print(f"API request failed: {e}")
            return None

# Function to determine the outcome of the game
def resolve_market(game_date, team1, team2):
    date_str = game_date.strftime("%Y-%m-%d")
    games = get_api_data(f"/GamesByDate/{date_str}", proxy=True)
    if games:
        for game in games:
            if {game["HomeTeam"], game["AwayTeam"]} == {team1, team2}:
                if game["Status"] == "Final":
                    home_score = game["HomeTeamRuns"]
                    away_score = game["AwayTeamRuns"]
                    if home_score > away_score:
                        winner = game["HomeTeam"]
                    else:
                        winner = game["AwayTeam"]
                    return "p1" if winner == team1 else "p2"
                elif game["Status"] in ["Canceled", "Postponed"]:
                    return "p3"
    return "p4"

# Main execution block
if __name__ == "__main__":
    # Define the game details
    game_date = datetime.strptime("2025-04-23", "%Y-%m-%d")
    team1 = "TEX"  # Texas Rangers
    team2 = "OAK"  # Oakland Athletics

    # Resolve the market based on the game outcome
    result = resolve_market(game_date, team1, team2)
    print(f"recommendation: {result}")