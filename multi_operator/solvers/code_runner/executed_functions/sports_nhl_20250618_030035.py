import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
NHL_API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
if not NHL_API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NHL_API_KEY")

# Configuration for API headers
HEADERS = {"Ocp-Apim-Subscription-Key": NHL_API_KEY}

# Constants for the event
GAME_DATE = "2025-06-17"
PLAYER_NAME = "Evan Bouchard"
TEAMS = ["EDM", "FLA"]  # Edmonton Oilers and Florida Panthers

# Resolution map based on the ancillary data
RESOLUTION_MAP = {
    "Yes": "p2",
    "No": "p1",
    "50-50": "p3"
}

def get_game_data(date):
    """Fetch game data for a specific date."""
    url = f"https://api.sportsdata.io/v3/nhl/scores/json/GamesByDate/{date}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    else:
        return None

def check_player_goals(games, player_name):
    """Check if the specified player scored a goal."""
    for game in games:
        if game['HomeTeam'] in TEAMS and game['AwayTeam'] in TEAMS:
            game_id = game['GameID']
            url = f"https://api.sportsdata.io/v3/nhl/stats/json/PlayerGameStatsByGame/{game_id}"
            response = requests.get(url, headers=HEADERS)
            if response.status_code == 200:
                player_stats = response.json()
                for stat in player_stats:
                    if stat['Name'] == player_name and stat['Goals'] > 0:
                        return True
    return False

def resolve_market():
    """Resolve the market based on the player's performance."""
    today = datetime.utcnow().date().isoformat()
    if today > GAME_DATE:
        games = get_game_data(GAME_DATE)
        if games:
            scored = check_player_goals(games, PLAYER_NAME)
            return "recommendation: " + RESOLUTION_MAP["Yes"] if scored else "recommendation: " + RESOLUTION_MAP["No"]
        else:
            return "recommendation: " + RESOLUTION_MAP["50-50"]
    else:
        return "recommendation: " + RESOLUTION_MAP["50-50"]

if __name__ == "__main__":
    result = resolve_market()
    print(result)