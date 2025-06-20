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
GAME_DATE = "2025-06-12"
PLAYER_NAME = "Leon Draisaitl"
TEAM_ABBREVIATIONS = {"Edmonton Oilers": "EDM", "Florida Panthers": "FLA"}

# API Configuration
HEADERS = {"Ocp-Apim-Subscription-Key": NHL_API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nhl"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/nhl-proxy"

# Function to make API requests
def make_request(url, headers, use_proxy=False):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if use_proxy:
            print(f"Error with primary endpoint, trying proxy. Error: {e}")
            return make_request(PROXY_ENDPOINT + url, headers)
        else:
            print(f"Failed to retrieve data: {e}")
            return None

# Function to find and analyze the game
def analyze_game():
    date_formatted = datetime.strptime(GAME_DATE, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = f"{PRIMARY_ENDPOINT}/scores/json/GamesByDate/{date_formatted}"
    games = make_request(url, HEADERS)

    if games is None:
        return "p4"  # Unable to retrieve data

    for game in games:
        if {game["HomeTeam"], game["AwayTeam"]} == set(TEAM_ABBREVIATIONS.values()):
            if game["Status"] == "Final":
                # Check player stats
                game_id = game["GameID"]
                player_stats_url = f"{PRIMARY_ENDPOINT}/stats/json/PlayerGameStatsByGame/{game_id}"
                player_stats = make_request(player_stats_url, HEADERS)

                if player_stats is None:
                    return "p4"  # Unable to retrieve player stats

                for stat in player_stats:
                    if stat["Name"] == PLAYER_NAME and stat["Goals"] > 0.5:
                        return "p2"  # Player scored more than 0.5 goals
                return "p1"  # Player did not score more than 0.5 goals
            elif game["Status"] in ["Scheduled", "InProgress"]:
                return "p4"  # Game not completed
            elif game["Status"] in ["Postponed", "Canceled"]:
                return "p3"  # Game not completed by the deadline
    return "p4"  # Game not found or other issues

# Main execution
if __name__ == "__main__":
    result = analyze_game()
    print(f"recommendation: {result}")