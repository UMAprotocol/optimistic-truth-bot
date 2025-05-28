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
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/mlb-proxy"

# Resolution map based on the game outcome
RESOLUTION_MAP = {
    "White Sox": "p2",
    "Mets": "p1",
    "Postponed": "p4",
    "Canceled": "p3",
    "Unknown": "p3"
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

# Function to find the game and determine the outcome
def resolve_game(date, team1, team2):
    formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = f"{PRIMARY_ENDPOINT}/GamesByDate/{formatted_date}"
    games = make_api_request(url)
    if games is None:
        print("Using proxy endpoint due to primary endpoint failure.")
        url = f"{PROXY_ENDPOINT}/GamesByDate/{formatted_date}"
        games = make_api_request(url)
        if games is None:
            return "p4"  # Unable to resolve due to API failure

    for game in games:
        if (game["HomeTeam"] == team1 and game["AwayTeam"] == team2) or (game["HomeTeam"] == team2 and game["AwayTeam"] == team1):
            if game["Status"] == "Final":
                if game["HomeTeamRuns"] > game["AwayTeamRuns"]:
                    winner = game["HomeTeam"]
                else:
                    winner = game["AwayTeam"]
                return RESOLUTION_MAP.get(winner, "p3")
            elif game["Status"] == "Postponed":
                return "p4"  # Game postponed, market remains open
            elif game["Status"] == "Canceled":
                return "p3"  # Game canceled, resolve as 50-50
    return "p4"  # No game found or not yet played

# Main execution
if __name__ == "__main__":
    game_date = "2025-05-27"
    home_team = "Mets"
    away_team = "White Sox"
    recommendation = resolve_game(game_date, home_team, away_team)
    print(f"recommendation: {recommendation}")