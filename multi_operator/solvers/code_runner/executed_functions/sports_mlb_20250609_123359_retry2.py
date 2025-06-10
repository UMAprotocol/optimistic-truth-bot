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
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-proxy/mlb"

# Resolution map
RESOLUTION_MAP = {
    "Dodgers": "p2",
    "Guardians": "p1",
    "50-50": "p3",
    "Too early to resolve": "p4"
}

# Helper function to make API requests
def make_api_request(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        # Fallback to proxy if primary fails
        proxy_url = PROXY_ENDPOINT + url[len(PRIMARY_ENDPOINT):]
        response = requests.get(proxy_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()

# Function to find the game and determine the outcome
def resolve_game(date, team1, team2):
    formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m-%d")
    games_today_url = f"{PRIMARY_ENDPOINT}/GamesByDate/{formatted_date}"
    games = make_api_request(games_today_url)

    for game in games:
        if {game["HomeTeam"], game["AwayTeam"]} == {team1, team2}:
            if game["Status"] == "Final":
                if game["HomeTeamRuns"] > game["AwayTeamRuns"]:
                    winner = game["HomeTeam"]
                else:
                    winner = game["AwayTeam"]
                return RESOLUTION_MAP.get(winner, "p4")
            elif game["Status"] in ["Canceled", "Postponed"]:
                return "p3"
            else:
                return "p4"
    return "p4"

# Main execution
if __name__ == "__main__":
    game_date = "2025-05-28"
    team1_key = "CLE"  # Cleveland Guardians
    team2_key = "LAD"  # Los Angeles Dodgers
    result = resolve_game(game_date, team1_key, team2_key)
    print(f"recommendation: {result}")