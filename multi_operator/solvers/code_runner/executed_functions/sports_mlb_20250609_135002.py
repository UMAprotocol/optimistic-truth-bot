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

# Function to handle API requests with a fallback mechanism
def get_api_response(endpoint, path):
    url = f"{endpoint}/{path}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if endpoint == PROXY_ENDPOINT:
            print(f"Falling back to primary endpoint due to error: {e}")
            return get_api_response(PRIMARY_ENDPOINT, path)
        else:
            print(f"API request failed: {e}")
            return None

# Function to determine the outcome of the game
def resolve_market(date_str, team1, team2):
    games_today = get_api_response(PROXY_ENDPOINT, f"GamesByDate/{date_str}")
    if games_today is None:
        return "recommendation: p4"  # Unable to resolve due to API failure

    for game in games_today:
        if {game["HomeTeam"], game["AwayTeam"]} == {team1, team2}:
            if game["Status"] == "Final":
                if game["HomeTeamRuns"] > game["AwayTeamRuns"]:
                    winner = game["HomeTeam"]
                else:
                    winner = game["AwayTeam"]
                if winner == team1:
                    return "recommendation: p1"
                elif winner == team2:
                    return "recommendation: p2"
            elif game["Status"] in ["Canceled", "Postponed"]:
                return "recommendation: p3"
            else:
                return "recommendation: p4"  # Game not final
    return "recommendation: p4"  # No matching game found

# Main execution block
if __name__ == "__main__":
    # Extracting the specific game details from the question
    date_of_game = "2025-05-29"
    team1 = "Royal Challengers Bangalore"
    team2 = "Punjab Kings"

    # Convert date to the required format
    game_date = datetime.strptime(date_of_game, "%Y-%m-%d").strftime("%Y-%m-%d")

    # Resolve the market based on the game outcome
    result = resolve_market(game_date, team1, team2)
    print(result)