import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
NHL_API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
if not NHL_API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NHL_API_KEY")

# Constants
GAME_DATE = "2025-06-17"
PLAYER_NAME = "Corey Perry"
TEAM_ABBREVIATIONS = {"Edmonton Oilers": "EDM", "Florida Panthers": "FLA"}

# Headers for API requests
HEADERS = {"Ocp-Apim-Subscription-Key": NHL_API_KEY}

# API Endpoints
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nhl"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-nhl-proxy"

# Function to make API requests
def make_request(url, headers):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

# Function to find and analyze the game
def analyze_game():
    # Construct the URL for the game date
    url = f"{PRIMARY_ENDPOINT}/scores/json/GamesByDate/{GAME_DATE}"
    games = make_request(url, HEADERS)
    if not games:
        print("Failed to retrieve games data.")
        return "p4"

    # Find the specific game
    for game in games:
        if game['HomeTeam'] in TEAM_ABBREVIATIONS.values() and game['AwayTeam'] in TEAM_ABBREVIATIONS.values():
            if game['Status'] == "Final":
                # Check player's performance
                player_stats_url = f"{PRIMARY_ENDPOINT}/stats/json/PlayerGameStatsByDate/{GAME_DATE}/{PLAYER_NAME}"
                player_stats = make_request(player_stats_url, HEADERS)
                if player_stats and any(stat['Goals'] > 0 for stat in player_stats):
                    return "p2"  # Player scored a goal
                else:
                    return "p1"  # Player did not score a goal
            elif game['Status'] in ["Scheduled", "InProgress"]:
                return "p4"  # Game not completed
            elif game['Status'] in ["Canceled", "Postponed"]:
                return "p3"  # Game not played
    return "p4"  # No relevant game found or game not yet played

# Main execution
if __name__ == "__main__":
    result = analyze_game()
    print(f"recommendation: {result}")