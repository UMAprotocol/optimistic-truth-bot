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
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

# Function to make API requests
def make_request(endpoint, path):
    try:
        response = requests.get(f"{endpoint}/{path}", headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

# Function to find the game and determine the outcome
def find_game_and_determine_outcome(date, team1, team2):
    games_today = make_request(PRIMARY_ENDPOINT, f"GamesByDate/{date}")
    if not games_today:
        return "p4"  # Unable to retrieve data

    for game in games_today:
        if {game["HomeTeam"], game["AwayTeam"]} == {team1, team2}:
            if game["Status"] == "Final":
                if game["HomeTeamRuns"] > game["AwayTeamRuns"]:
                    return "p1" if game["HomeTeam"] == team1 else "p2"
                elif game["HomeTeamRuns"] < game["AwayTeamRuns"]:
                    return "p1" if game["AwayTeam"] == team1 else "p2"
            elif game["Status"] in ["Canceled", "Postponed"]:
                return "p3"
            return "p4"  # Game not final
    return "p4"  # No matching game found

# Main execution function
def main():
    # Define the game specifics
    date = "2025-05-29"
    team1 = "Royal Challengers Bangalore"
    team2 = "Punjab Kings"

    # Attempt to use the proxy endpoint first
    result = find_game_and_determine_outcome(date, team1, team2)
    if result is None:
        # Fallback to primary endpoint if proxy fails
        result = find_game_and_determine_outcome(date, team1, team2)

    # Print the recommendation based on the result
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()