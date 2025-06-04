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
GAME_DATE = "2025-06-03"
TEAMS = {"Twins": "MIN", "Athletics": "OAK"}

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
        games_today = make_request(PROXY_ENDPOINT, f"GamesByDate/{date_formatted}")

    if games_today:
        for game in games_today:
            if game["HomeTeam"] in TEAMS.values() and game["AwayTeam"] in TEAMS.values():
                if game["Status"] == "Final":
                    home_runs = game["HomeTeamRuns"]
                    away_runs = game["AwayTeamRuns"]
                    if home_runs > away_runs:
                        return "Twins" if game["HomeTeam"] == TEAMS["Twins"] else "Athletics"
                    else:
                        return "Athletics" if game["AwayTeam"] == TEAMS["Athletics"] else "Twins"
                elif game["Status"] == "Canceled":
                    return "50-50"
                elif game["Status"] == "Postponed":
                    return "Postponed"
    return "Too early to resolve"

# Main execution
if __name__ == "__main__":
    result = resolve_game()
    if result == "Twins":
        print("recommendation: p2")
    elif result == "Athletics":
        print("recommendation: p1")
    elif result == "50-50":
        print("recommendation: p3")
    elif result == "Postponed":
        print("recommendation: p4")
    else:
        print("recommendation: p4")