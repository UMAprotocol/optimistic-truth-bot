import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# Configuration for headers and endpoints
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/mlb/scores/json"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

# Function to handle API requests with fallback mechanism
def get_api_response(url, headers, retries=3):
    proxy_url = f"{PROXY_ENDPOINT}{url}"
    for attempt in range(retries):
        try:
            response = requests.get(proxy_url, headers=headers, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception("Proxy failed")
        except:
            if attempt < retries - 1:
                continue
            else:
                response = requests.get(f"{PRIMARY_ENDPOINT}{url}", headers=headers, timeout=10)
                if response.status_code == 200:
                    return response.json()
                else:
                    response.raise_for_status()

# Function to find the game and determine the outcome
def resolve_game(date, team1, team2):
    date_formatted = datetime.strptime(date, "%Y-%m-%d").date()
    games_today = get_api_response(f"/GamesByDate/{date_formatted}", HEADERS)
    for game in games_today:
        if {game["HomeTeam"], game["AwayTeam"]} == {team1, team2}:
            if game["Status"] == "Final":
                home_runs = game["HomeTeamRuns"]
                away_runs = game["AwayTeamRuns"]
                if home_runs == away_runs:
                    return "p3"  # Tie
                elif (home_runs > away_runs and game["HomeTeam"] == team1) or (away_runs > home_runs and game["AwayTeam"] == team1):
                    return "p1"  # Team1 wins
                else:
                    return "p2"  # Team2 wins
            elif game["Status"] in ["Canceled", "Postponed"]:
                return "p3"  # Game canceled or postponed
            else:
                return "p4"  # Game not final
    return "p4"  # No game found or in progress

# Main execution block
if __name__ == "__main__":
    # Example data, replace with dynamic data extraction if needed
    date = "2025-04-23"
    team1 = "TEX"  # Texas Rangers
    team2 = "OAK"  # Oakland Athletics

    recommendation = resolve_game(date, team1, team2)
    print(f"recommendation: {recommendation}")