import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
NHL_API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
if not NHL_API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NHL_API_KEY")

# API configuration
HEADERS = {"Ocp-Apim-Subscription-Key": NHL_API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nhl"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

# Resolution map based on team abbreviations
RESOLUTION_MAP = {
    "CAR": "p2",  # Carolina Hurricanes
    "FLA": "p1",  # Florida Panthers
    "50-50": "p3",
    "Too early to resolve": "p4",
}

# Function to make API requests
def make_request(url, headers, timeout=10):
    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

# Function to find the game and determine the outcome
def find_game_and_determine_outcome(date_str):
    formatted_date = datetime.strptime(date_str, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = f"{PRIMARY_ENDPOINT}/scores/json/GamesByDate/{formatted_date}"
    games = make_request(url, HEADERS)
    
    if games is None:
        return "p4"  # Unable to resolve due to API error

    for game in games:
        if {game["HomeTeam"], game["AwayTeam"]} == {"CAR", "FLA"}:
            if game["Status"] == "Final":
                if game["HomeTeam"] == "CAR" and game["HomeTeamScore"] > game["AwayTeamScore"]:
                    return RESOLUTION_MAP["CAR"]
                elif game["AwayTeam"] == "CAR" and game["AwayTeamScore"] > game["HomeTeamScore"]:
                    return RESOLUTION_MAP["CAR"]
                elif game["HomeTeam"] == "FLA" and game["HomeTeamScore"] > game["AwayTeamScore"]:
                    return RESOLUTION_MAP["FLA"]
                elif game["AwayTeam"] == "FLA" and game["AwayTeamScore"] > game["HomeTeamScore"]:
                    return RESOLUTION_MAP["FLA"]
            elif game["Status"] == "Postponed":
                return "p4"  # Game postponed, resolution pending
            elif game["Status"] == "Canceled":
                return RESOLUTION_MAP["50-50"]
    return "p4"  # Game not found or not yet played

# Main execution function
if __name__ == "__main__":
    game_date = "2025-05-24"
    recommendation = find_game_and_determine_outcome(game_date)
    print(f"recommendation: {recommendation}")