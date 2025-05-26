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
def make_request(url, use_proxy=False):
    endpoint = PROXY_ENDPOINT if use_proxy else PRIMARY_ENDPOINT
    full_url = f"{endpoint}{url}"
    try:
        response = requests.get(full_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if use_proxy:
            print("Proxy failed, trying primary endpoint.")
            return make_request(url, use_proxy=False)
        else:
            print(f"Failed to retrieve data: {e}")
            return None

# Function to find the game and determine the outcome
def resolve_market(date_str, team1, team2):
    games_today = make_request(f"/GamesByDate/{date_str}")
    if games_today is None:
        return "p4"  # Unable to retrieve data

    for game in games_today:
        if {game["HomeTeam"], game["AwayTeam"]} == {team1, team2}:
            if game["Status"] == "Final":
                if game["HomeTeamRuns"] > game["AwayTeamRuns"]:
                    winner = game["HomeTeam"]
                else:
                    winner = game["AwayTeam"]
                
                if winner == team1:
                    return "p1"
                elif winner == team2:
                    return "p2"
            elif game["Status"] in ["Canceled", "Postponed"]:
                return "p3"
            else:
                return "p4"  # Game not final or other status

    return "p4"  # No matching game found

# Main execution function
if __name__ == "__main__":
    # Extracted information from the question
    date_of_game = "2025-05-13"
    team1 = "Sunrisers Hyderabad"
    team2 = "Royal Challengers Bangalore"

    # Convert date to required format
    formatted_date = datetime.strptime(date_of_game, "%Y-%m-%d").strftime("%Y-%m-%d")

    # Resolve the market based on the game outcome
    result = resolve_market(formatted_date, team1, team2)
    print(f"recommendation: {result}")