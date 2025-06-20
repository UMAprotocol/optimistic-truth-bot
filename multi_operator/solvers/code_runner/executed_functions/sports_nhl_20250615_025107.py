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
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nhl"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/nhl-proxy"

# Headers for API requests
HEADERS = {"Ocp-Apim-Subscription-Key": NHL_API_KEY}

# Game and player details
GAME_DATE = "2025-06-14"
PLAYER_NAME = "Carter Verhaeghe"
TEAMS = {"Edmonton Oilers": "EDM", "Florida Panthers": "FLA"}

# Resolution conditions
RESOLUTION_MAP = {
    "Yes": "p2",  # Player scores more than 0.5 goals
    "No": "p1",   # Player does not score more than 0.5 goals
    "50-50": "p3" # Game not completed by the deadline
}

def get_game_data(date, teams):
    """Retrieve game data for the specified date and teams."""
    formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = f"{PRIMARY_ENDPOINT}/scores/json/GamesByDate/{formatted_date}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        games = response.json()
        for game in games:
            if game['HomeTeam'] in teams.values() and game['AwayTeam'] in teams.values():
                return game
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from primary endpoint: {e}")
        try:
            response = requests.get(PROXY_ENDPOINT, headers=HEADERS, timeout=10)
            response.raise_for_status()
            games = response.json()
            for game in games:
                if game['HomeTeam'] in teams.values() and game['AwayTeam'] in teams.values():
                    return game
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data from proxy endpoint: {e}")
    return None

def check_player_goals(game_id, player_name):
    """Check if the specified player scored a goal in the game."""
    url = f"{PRIMARY_ENDPOINT}/stats/json/PlayerGameStatsByGame/{game_id}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        player_stats = response.json()
        for stat in player_stats:
            if stat['Name'] == player_name:
                return stat['Goals'] > 0.5
    except requests.exceptions.RequestException as e:
        print(f"Error fetching player stats: {e}")
    return False

def resolve_market():
    """Resolve the market based on the player's performance and game completion."""
    game = get_game_data(GAME_DATE, TEAMS)
    if not game:
        return "recommendation: " + RESOLUTION_MAP["50-50"]
    if game['Status'] != 'Final':
        return "recommendation: " + RESOLUTION_MAP["50-50"]
    if check_player_goals(game['GameId'], PLAYER_NAME):
        return "recommendation: " + RESOLUTION_MAP["Yes"]
    else:
        return "recommendation: " + RESOLUTION_MAP["No"]

if __name__ == "__main__":
    print(resolve_market())