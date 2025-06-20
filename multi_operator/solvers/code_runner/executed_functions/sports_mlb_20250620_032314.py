import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NBA_API_KEY")

# Configuration for headers and endpoints
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nba"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-nba-proxy"

# Date and game details
GAME_DATE = "2025-06-19"
PLAYER_NAME = "Tyrese Haliburton"
TEAM_VS = "Oklahoma City Thunder"

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

# Function to find the game and check player's score
def check_player_score():
    # Convert game date to datetime object
    game_datetime = datetime.strptime(GAME_DATE, "%Y-%m-%d")
    formatted_date = game_datetime.strftime("%Y-%m-%d")

    # Get games by date
    games = make_request(f"/scores/json/GamesByDate/{formatted_date}", use_proxy=True)
    if not games:
        return "p4"  # Unable to retrieve data

    # Find the specific game
    for game in games:
        if TEAM_VS in (game['HomeTeam'], game['AwayTeam']):
            # Check if game status is not final
            if game['Status'] != 'Final':
                return "p1"  # Game not completed or player did not play

            # Get game box score
            game_id = game['GameID']
            box_score = make_request(f"/stats/json/PlayerGameStatsByGame/{game_id}", use_proxy=True)
            if not box_score:
                return "p4"  # Unable to retrieve box score

            # Check player's score
            for player_stats in box_score:
                if player_stats['Name'] == PLAYER_NAME:
                    points = player_stats['Points']
                    return "p2" if points > 15.5 else "p1"

    return "p1"  # Game not found or player did not play

# Main execution
if __name__ == "__main__":
    result = check_player_score()
    print(f"recommendation: {result}")