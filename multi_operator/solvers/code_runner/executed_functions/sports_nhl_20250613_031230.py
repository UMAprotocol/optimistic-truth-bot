import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NHL_API_KEY")

# Constants
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nhl"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/nhl-proxy"
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
GAME_DATE = "2025-06-10"
TEAMS = {"Florida Panthers": "FLA", "Edmonton Oilers": "EDM"}
RESOLUTION_MAP = {"No": "p1", "Yes": "p2", "50-50": "p3"}

# Function to make API requests
def make_request(endpoint, path):
    try:
        response = requests.get(f"{endpoint}{path}", headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return None

# Function to check if game went to overtime
def check_overtime(game_data):
    if game_data:
        for game in game_data:
            if game["HomeTeam"] == TEAMS["Florida Panthers"] and game["AwayTeam"] == TEAMS["Edmonton Oilers"]:
                if game["IsOvertime"]:
                    return "Yes"
        return "No"
    return "50-50"

# Main function to resolve the market
def resolve_market():
    date_str = datetime.strptime(GAME_DATE, "%Y-%m-%d").strftime("%Y-%m-%d")
    path = f"/scores/json/GamesByDate/{date_str}"

    # Try proxy endpoint first
    game_data = make_request(PROXY_ENDPOINT, path)
    if game_data is None:
        # Fallback to primary endpoint
        game_data = make_request(PRIMARY_ENDPOINT, path)

    # Determine the outcome
    result = check_overtime(game_data)
    return f"recommendation: {RESOLUTION_MAP[result]}"

# Run the resolver
if __name__ == "__main__":
    print(resolve_market())