import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NHL_API_KEY")
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

# Constants
GAME_DATE = "2025-06-14"
PLAYER_NAME = "Aleksander Barkov"
TEAM_ABBREVIATIONS = {"Edmonton Oilers": "EDM", "Florida Panthers": "FLA"}

# Resolution map based on the ancillary data provided
RESOLUTION_MAP = {
    "Yes": "p2",  # Player scored more than 0.5 goals
    "No": "p1",   # Player did not score more than 0.5 goals
    "50-50": "p3" # Game not completed by the specified date
}

# Helper function to make API requests
def make_request(url, tag, fallback_url=None):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if fallback_url:
            try:
                response = requests.get(fallback_url, headers=HEADERS, timeout=10)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException:
                pass
        print(f"Error during {tag}: {str(e)}")
        return None

# Function to check if the player scored a goal
def check_player_goals():
    # Construct the URL for the game data
    primary_url = f"https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/{GAME_DATE}"
    proxy_url = "https://minimal-ubuntu-production.up.railway.app/nhl-proxy/GamesByDate/" + GAME_DATE

    # Make the API request
    games = make_request(primary_url, "NHL Game Data", fallback_url=proxy_url)
    if not games:
        return "50-50"  # Unable to retrieve data

    # Find the specific game
    for game in games:
        if {game["HomeTeam"], game["AwayTeam"]} == set(TEAM_ABBREVIATIONS.values()):
            if datetime.now() < datetime.strptime(game["Day"], "%Y-%m-%dT%H:%M:%S"):
                return "Too early to resolve"
            # Check player stats
            player_stats_url = f"https://api.sportsdata.io/v3/nhl/stats/json/PlayerGameStatsByDate/{GAME_DATE}/{PLAYER_NAME}"
            player_stats = make_request(player_stats_url, "Player Stats")
            if player_stats and player_stats[0]["Goals"] > 0.5:
                return "Yes"
            else:
                return "No"

    return "50-50"  # Game not found or not completed

# Main execution
if __name__ == "__main__":
    result = check_player_goals()
    print("recommendation:", RESOLUTION_MAP[result])