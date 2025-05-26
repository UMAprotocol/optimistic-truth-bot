import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API keys loaded from environment variables
SPORTS_DATA_IO_MLB_API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")

# Headers for API requests
HEADERS = {"Ocp-Apim-Subscription-Key": SPORTS_DATA_IO_MLB_API_KEY}

# API endpoints
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/mlb/scores/json"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

# Function to make API requests
def make_api_request(url, use_proxy=False):
    endpoint = PROXY_ENDPOINT if use_proxy else PRIMARY_ENDPOINT
    try:
        response = requests.get(f"{endpoint}{url}", headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if use_proxy:
            print("Proxy failed, trying primary endpoint.")
            return make_api_request(url, use_proxy=False)
        else:
            print(f"API request failed: {e}")
            return None

# Function to find the game and determine the outcome
def find_game_and_determine_outcome(date, team1, team2):
    games = make_api_request(f"/GamesByDate/{date}")
    if games is None:
        return "p4"  # Unable to retrieve data

    for game in games:
        if {game["HomeTeam"], game["AwayTeam"]} == {team1, team2}:
            if game["Status"] == "Final":
                home_score = game["HomeTeamRuns"]
                away_score = game["AwayTeamRuns"]
                if home_score == away_score:
                    return "p3"  # Tie
                elif (home_score > away_score and team1 == game["HomeTeam"]) or (away_score > home_score and team1 == game["AwayTeam"]):
                    return "p1"  # Team1 wins
                else:
                    return "p2"  # Team2 wins
            else:
                return "p3"  # Game not final, consider as tie/canceled
    return "p4"  # Game not found or in progress

# Main execution function
def main():
    # Example data, normally this would be dynamically determined
    date = "2025-04-23"
    team1 = "TEX"  # Texas Rangers
    team2 = "OAK"  # Oakland Athletics

    recommendation = find_game_and_determine_outcome(date, team1, team2)
    print(f"recommendation: {recommendation}")

if __name__ == "__main__":
    main()