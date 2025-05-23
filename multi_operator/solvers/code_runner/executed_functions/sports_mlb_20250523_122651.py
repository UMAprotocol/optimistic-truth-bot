import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# API configuration
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/mlb/scores/json"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

# Game details
GAME_DATE = "2025-05-22"
TEAMS = {"Angels": "p2", "Athletics": "p1"}

# Function to make API requests
def make_request(endpoint, path):
    url = f"{endpoint}/{path}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

# Function to find the game and determine the outcome
def resolve_game():
    date_formatted = datetime.strptime(GAME_DATE, "%Y-%m-%d").strftime("%Y-%m-%d")
    games_today = make_request(PRIMARY_ENDPOINT, f"GamesByDate/{date_formatted}")

    if not games_today:
        print("Failed to retrieve games data. Trying proxy...")
        games_today = make_request(PROXY_ENDPOINT, f"GamesByDate/{date_formatted}")

    if not games_today:
        return "recommendation: p4"  # Unable to retrieve data

    for game in games_today:
        if game["HomeTeam"] in TEAMS and game["AwayTeam"] in TEAMS:
            if game["Status"] == "Final":
                home_team_runs = game["HomeTeamRuns"]
                away_team_runs = game["AwayTeamRuns"]
                if home_team_runs > away_team_runs:
                    return f"recommendation: {TEAMS[game['HomeTeam']]}"
                else:
                    return f"recommendation: {TEAMS[game['AwayTeam']]}"
            elif game["Status"] == "Canceled":
                return "recommendation: p3"
            elif game["Status"] == "Postponed":
                return "recommendation: p4"

    return "recommendation: p4"  # No matching game found or game not yet played

# Main execution
if __name__ == "__main__":
    result = resolve_game()
    print(result)