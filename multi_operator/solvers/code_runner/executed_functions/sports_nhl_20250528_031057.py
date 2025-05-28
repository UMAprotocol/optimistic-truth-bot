import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NHL_API_KEY")

# Configuration
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
DATE = "2025-05-27"
TEAM_ABBR = "EDM"  # Edmonton Oilers
OPPONENT_ABBR = "DAL"  # Dallas Stars
PLAYER_NAME = "Connor McDavid"

# NHL API endpoints
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nhl"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-nhl-proxy"

# Function to make API requests
def make_request(url, headers):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error during request: {e}")
        return None

# Function to check player's performance
def check_player_performance(game_id, player_name):
    url = f"{PRIMARY_ENDPOINT}/scores/json/PlayerGameStatsByGame/{game_id}"
    game_stats = make_request(url, HEADERS)
    if game_stats:
        for stat in game_stats:
            if stat['Name'] == player_name and stat['Goals'] >= 1:
                return True
    return False

# Function to find the game and check if the player scored
def resolve_market():
    date_formatted = datetime.strptime(DATE, "%Y-%m-%d").strftime("%Y-%b-%d")
    url = f"{PRIMARY_ENDPOINT}/scores/json/GamesByDate/{date_formatted}"
    games = make_request(url, HEADERS)
    if games:
        for game in games:
            if game['HomeTeam'] == TEAM_ABBR or game['AwayTeam'] == TEAM_ABBR:
                if game['Status'] == "Final":
                    if check_player_performance(game['GameID'], PLAYER_NAME):
                        return "recommendation: p2"  # Player scored
                    else:
                        return "recommendation: p1"  # Player did not score
                else:
                    return "recommendation: p1"  # Game not final or player did not play
    return "recommendation: p1"  # No game found or other conditions not met

# Main execution
if __name__ == "__main__":
    result = resolve_market()
    print(result)