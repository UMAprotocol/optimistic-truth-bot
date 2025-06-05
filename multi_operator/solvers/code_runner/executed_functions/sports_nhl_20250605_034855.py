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
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-nhl-proxy"

# Game and player details
GAME_DATE = "2025-06-04"
TEAM_ABBR_EDMONTON = "EDM"
TEAM_ABBR_FLORIDA = "FLA"
PLAYER_NAME = "Connor McDavid"

# Function to make API requests
def make_request(url, use_proxy=False):
    endpoint = PROXY_ENDPOINT if use_proxy else PRIMARY_ENDPOINT
    full_url = f"{endpoint}{url}"
    try:
        response = requests.get(full_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if use_proxy:
            print("Proxy failed, trying primary endpoint.")
            return make_request(url, use_proxy=False)
        else:
            print(f"Failed to retrieve data: {e}")
            return None

# Function to check if McDavid scored in the specified game
def check_mcdavid_score():
    # Fetch games by date
    games = make_request(f"/scores/json/GamesByDate/{GAME_DATE}")
    if not games:
        return "p4"  # Unable to retrieve game data

    # Find the specific game
    game = next((g for g in games if g['HomeTeam'] == TEAM_ABBR_FLORIDA and g['AwayTeam'] == TEAM_ABBR_EDMONTON), None)
    if not game:
        return "p1"  # Game not found or did not occur

    # Check game status
    if game['Status'] != 'Final':
        return "p1"  # Game not completed or cancelled

    # Fetch player game stats
    game_id = game['GameID']
    player_stats = make_request(f"/stats/json/PlayerGameStatsByGame/{game_id}")
    if not player_stats:
        return "p4"  # Unable to retrieve player stats

    # Check if McDavid scored
    mcdavid_stats = next((p for p in player_stats if p['Name'] == PLAYER_NAME), None)
    if not mcdavid_stats:
        return "p1"  # McDavid did not play

    goals = mcdavid_stats.get('Goals', 0)
    if goals >= 1:
        return "p2"  # McDavid scored 1 or more goals
    else:
        return "p1"  # McDavid did not score

# Main execution
if __name__ == "__main__":
    result = check_mcdavid_score()
    print(f"recommendation: {result}")