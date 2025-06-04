import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
MLB_API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not MLB_API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# API configuration
HEADERS = {"Ocp-Apim-Subscription-Key": MLB_API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/mlb/scores/json"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/mlb-proxy"

# Resolution map
RESOLUTION_MAP = {
    "Cubs": "p2",
    "Nationals": "p1",
    "50-50": "p3",
    "Too early to resolve": "p4"
}

# Function to make API requests
def make_api_request(endpoint, path):
    try:
        response = requests.get(f"{endpoint}/{path}", headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        return None

# Function to resolve the outcome based on game data
def resolve_outcome(game_data):
    if not game_data:
        return RESOLUTION_MAP["Too early to resolve"]
    if game_data["Status"] == "Final":
        home_team = game_data["HomeTeam"]
        away_team = game_data["AwayTeam"]
        home_score = game_data["HomeTeamRuns"]
        away_score = game_data["AwayTeamRuns"]
        if home_score > away_score:
            winner = home_team
        else:
            winner = away_team
        if winner == "CHC":
            return RESOLUTION_MAP["Cubs"]
        elif winner == "WAS":
            return RESOLUTION_MAP["Nationals"]
    elif game_data["Status"] in ["Canceled", "Postponed"]:
        return RESOLUTION_MAP["50-50"]
    return RESOLUTION_MAP["Too early to resolve"]

# Main function to process the game data
def process_game(date_str):
    date = datetime.strptime(date_str, "%Y-%m-%d").date()
    game_path = f"GamesByDate/{date}"

    # Try proxy endpoint first
    game_data = make_api_request(PROXY_ENDPOINT, game_path)
    if game_data is None:
        # Fallback to primary endpoint
        game_data = make_api_request(PRIMARY_ENDPOINT, game_path)

    # Resolve the outcome based on the game data
    return resolve_outcome(game_data)

# Example usage
if __name__ == "__main__":
    game_date = "2025-06-03"
    print("recommendation:", process_game(game_date))