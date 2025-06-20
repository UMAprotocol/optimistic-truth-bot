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
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/nhl-proxy"

# Game and player details
GAME_DATE = "2025-06-14"
PLAYER_NAME = "Evan Bouchard"
TEAM_ABBREVIATIONS = {"Edmonton Oilers": "EDM", "Florida Panthers": "FLA"}

# Resolution conditions
RESOLUTION_MAP = {
    "No": "p1",
    "Yes": "p2",
    "50-50": "p3",
    "Too early to resolve": "p4"
}

def get_game_data(date):
    """Fetch game data for the specified date."""
    url = f"{PRIMARY_ENDPOINT}/scores/json/GamesByDate/{date}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from primary endpoint: {e}")
        try:
            # Fallback to proxy endpoint
            response = requests.get(f"{PROXY_ENDPOINT}/scores/json/GamesByDate/{date}", headers=HEADERS, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data from proxy endpoint: {e}")
            return None

def check_player_goals(game_data, player_name):
    """Check if the specified player scored a goal."""
    for game in game_data:
        if game['Status'] == 'Final' and (game['HomeTeam'] == TEAM_ABBREVIATIONS["Edmonton Oilers"] or game['AwayTeam'] == TEAM_ABBREVIATIONS["Florida Panthers"]):
            for player in game['PlayerStats']:
                if player['Name'] == player_name and player['Goals'] > 0:
                    return True
    return False

def resolve_market():
    """Resolve the market based on the game data and player performance."""
    current_date = datetime.now().strftime("%Y-%m-%d")
    if current_date > "2025-12-31":
        return RESOLUTION_MAP["50-50"]

    game_data = get_game_data(GAME_DATE)
    if not game_data:
        return RESOLUTION_MAP["Too early to resolve"]

    player_scored = check_player_goals(game_data, PLAYER_NAME)
    if player_scored:
        return RESOLUTION_MAP["Yes"]
    else:
        return RESOLUTION_MAP["No"]

if __name__ == "__main__":
    result = resolve_market()
    print(f"recommendation: {result}")