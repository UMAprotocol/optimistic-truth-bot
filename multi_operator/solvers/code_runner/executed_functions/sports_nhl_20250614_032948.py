import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NBA_API_KEY")

# Configuration for API requests
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nba/scores/json"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/nba-proxy"

# Resolution map based on the ancillary data provided
RESOLUTION_MAP = {
    "OKC": "p2",  # Oklahoma City Thunder
    "IND": "p1",  # Indiana Pacers
    "Postponed": "p4",
    "Canceled": "p3"
}

# Function to make API requests
def make_api_request(url, params=None):
    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error during API request: {e}")
        return None

# Function to find the game and determine the outcome
def find_game_and_resolve(date_str):
    formatted_date = datetime.strptime(date_str, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = f"{PRIMARY_ENDPOINT}/GamesByDate/{formatted_date}"
    games = make_api_request(url)
    
    if games is None:
        print("Failed to retrieve data from primary endpoint, trying proxy...")
        url = f"{PROXY_ENDPOINT}/GamesByDate/{formatted_date}"
        games = make_api_request(url)
        if games is None:
            return "recommendation: p4"  # Unable to resolve due to API failure

    for game in games:
        if game["HomeTeam"] == "OKC" or game["AwayTeam"] == "OKC":
            if game["HomeTeam"] == "IND" or game["AwayTeam"] == "IND":
                if game["Status"] == "Final":
                    home_score = game["HomeTeamScore"]
                    away_score = game["AwayTeamScore"]
                    if home_score > away_score:
                        winner = game["HomeTeam"]
                    else:
                        winner = game["AwayTeam"]
                    return f"recommendation: {RESOLUTION_MAP[winner]}"
                elif game["Status"] == "Postponed":
                    return "recommendation: p4"  # Market remains open
                elif game["Status"] == "Canceled":
                    return "recommendation: p3"  # Resolve as 50-50
    return "recommendation: p4"  # Game not found or not yet played

# Main execution function
if __name__ == "__main__":
    game_date = "2025-06-13"
    result = find_game_and_resolve(game_date)
    print(result)