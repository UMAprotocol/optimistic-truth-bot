import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# Configuration for API requests
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/mlb"

# Game details
GAME_DATE = "2025-06-11"
HOME_TEAM = "Milwaukee Brewers"
AWAY_TEAM = "Atlanta Braves"

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

# Function to find and analyze the game
def analyze_game():
    date_formatted = datetime.strptime(GAME_DATE, "%Y-%m-%d").strftime("%Y-%m-%d")
    games_today = make_request(f"/scores/json/GamesByDate/{date_formatted}")

    if not games_today:
        return "p4"  # Unable to retrieve data

    for game in games_today:
        if game["HomeTeam"] == HOME_TEAM and game["AwayTeam"] == AWAY_TEAM:
            if game["Status"] == "Final":
                home_score = game["HomeTeamRuns"]
                away_score = game["AwayTeamRuns"]
                if home_score > away_score:
                    return "p1"  # Home team wins
                elif away_score > home_score:
                    return "p2"  # Away team wins
            elif game["Status"] == "Postponed":
                return "p4"  # Game postponed, check later
            elif game["Status"] == "Canceled":
                return "p3"  # Game canceled, resolve 50-50

    return "p4"  # No game found or not yet played

# Main execution
if __name__ == "__main__":
    result = analyze_game()
    print(f"recommendation: {result}")