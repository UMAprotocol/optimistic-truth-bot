import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NHL_API_KEY")

# Configuration for API requests
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nhl"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

# Team abbreviations and resolution map
TEAMS = {
    "Florida Panthers": "FLA",
    "Carolina Hurricanes": "CAR"
}
RESOLUTION_MAP = {
    "FLA": "p2",  # Panthers win
    "CAR": "p1",  # Hurricanes win
    "50-50": "p3",  # Game canceled or unresolved
    "Too early to resolve": "p4"  # Game not yet played or in progress
}

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
            print(f"Error: {e}")
            return None

# Function to determine the outcome of the game
def determine_outcome(game_date):
    formatted_date = datetime.strptime(game_date, "%Y-%m-%d").strftime("%Y-%m-%d")
    games_today = make_request(f"/scores/json/GamesByDate/{formatted_date}")

    if games_today:
        for game in games_today:
            if game['HomeTeam'] in TEAMS.values() and game['AwayTeam'] in TEAMS.values():
                if game['Status'] == "Final":
                    home_team = game['HomeTeam']
                    away_team = game['AwayTeam']
                    home_score = game['HomeTeamScore']
                    away_score = game['AwayTeamScore']
                    if home_score > away_score:
                        return RESOLUTION_MAP[home_team]
                    elif away_score > home_score:
                        return RESOLUTION_MAP[away_team]
                elif game['Status'] in ["Canceled", "Postponed"]:
                    return RESOLUTION_MAP["50-50"]
                else:
                    return RESOLUTION_MAP["Too early to resolve"]
    return RESOLUTION_MAP["Too early to resolve"]

# Main execution
if __name__ == "__main__":
    game_date = "2025-05-22"
    result = determine_outcome(game_date)
    print(f"recommendation: {result}")