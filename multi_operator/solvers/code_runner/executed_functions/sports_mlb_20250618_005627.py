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
GAME_DATE = "2025-06-17"
PHILLIES_KEY = "PHI"
MARLINS_KEY = "MIA"

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
        return "recommendation: p4"  # Unable to retrieve data

    for game in games_today:
        if {game["HomeTeam"], game["AwayTeam"]} == {PHILLIES_KEY, MARLINS_KEY}:
            if game["Status"] == "Final":
                if game["HomeTeamRuns"] > game["AwayTeamRuns"]:
                    winner = game["HomeTeam"]
                else:
                    winner = game["AwayTeam"]

                if winner == PHILLIES_KEY:
                    return "recommendation: p2"  # Phillies win
                elif winner == MARLINS_KEY:
                    return "recommendation: p1"  # Marlins win
            elif game["Status"] == "Postponed":
                return "recommendation: p4"  # Game postponed
            elif game["Status"] == "Canceled":
                return "recommendation: p3"  # Game canceled

    return "recommendation: p4"  # No matching game found or game not yet played

# Main execution
if __name__ == "__main__":
    result = resolve_game()
    print(result)