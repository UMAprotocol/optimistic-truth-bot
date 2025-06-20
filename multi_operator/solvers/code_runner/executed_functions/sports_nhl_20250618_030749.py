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
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nhl"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/nhl-proxy"
HEADERS = {"Ocp-Apim-Subscription-Key": NHL_API_KEY}
GAME_DATE = "2025-06-17"
TEAM_ABBREVIATIONS = {"Edmonton Oilers": "EDM", "Florida Panthers": "FLA"}
RESOLUTION_MAP = {"EDM": "p1", "FLA": "p2", "50-50": "p3", "Too early to resolve": "p4"}

# Helper function to make API requests
def make_request(url, headers):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

# Function to check if Corey Perry scored a goal
def check_corey_perry_goal():
    # Construct URL for the game data
    game_date_formatted = datetime.strptime(GAME_DATE, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = f"{PRIMARY_ENDPOINT}/scores/json/GamesByDate/{game_date_formatted}"

    # Try proxy endpoint first
    data = make_request(f"{PROXY_ENDPOINT}?url={url}", HEADERS)
    if not data:
        # Fallback to primary endpoint if proxy fails
        data = make_request(url, HEADERS)

    if not data:
        return "p4"  # Unable to retrieve data

    # Find the game and check for Corey Perry's goals
    for game in data:
        if {game["HomeTeam"], game["AwayTeam"]} == {"EDM", "FLA"}:
            if game["Status"] != "Final":
                return "p4"  # Game not completed
            # Check player stats
            player_stats_url = f"{PRIMARY_ENDPOINT}/stats/json/PlayerGameStatsByDate/{game_date_formatted}"
            player_stats = make_request(player_stats_url, HEADERS)
            if player_stats:
                for stat in player_stats:
                    if stat["Name"] == "Corey Perry" and stat["Goals"] > 0:
                        return "p2"  # Corey Perry scored
            return "p1"  # Corey Perry did not score
    return "p4"  # Game not found or other issue

# Main execution
if __name__ == "__main__":
    result = check_corey_perry_goal()
    print(f"recommendation: {result}")