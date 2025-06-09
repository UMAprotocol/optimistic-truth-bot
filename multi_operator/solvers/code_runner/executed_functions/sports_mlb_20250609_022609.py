import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NBA_API_KEY")

# Configuration
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
DATE = "2025-06-08"
PLAYER_NAME = "Tyrese Haliburton"
TEAM1 = "Indiana Pacers"
TEAM2 = "Oklahoma City Thunder"
GAME_ID = "550401"  # Example game ID, replace with actual if available

# API Endpoints
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nba"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-nba-proxy"

# Function to make API requests
def make_request(url, headers, timeout=10):
    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error during request: {e}")
        return None

# Function to find player stats in a specific game
def get_player_game_stats(date, player_name):
    formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = f"{PROXY_ENDPOINT}/scores/json/PlayerGameStatsByDate/{formatted_date}"
    data = make_request(url, HEADERS)
    if not data:
        url = f"{PRIMARY_ENDPOINT}/scores/json/PlayerGameStatsByDate/{formatted_date}"
        data = make_request(url, HEADERS)
    if data:
        for item in data:
            if item["Name"] == player_name:
                return item
    return None

# Main function to determine the outcome
def resolve_market():
    stats = get_player_game_stats(DATE, PLAYER_NAME)
    if stats and stats["Points"] > 16.5:
        return "recommendation: p2"  # Yes, scored more than 16.5 points
    elif stats and stats["Points"] <= 16.5:
        return "recommendation: p1"  # No, did not score more than 16.5 points
    else:
        return "recommendation: p1"  # No data or did not play, resolve as No

# Run the main function
if __name__ == "__main__":
    result = resolve_market()
    print(result)