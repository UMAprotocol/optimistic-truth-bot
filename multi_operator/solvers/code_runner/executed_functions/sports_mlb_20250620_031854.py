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

# Date and team configuration
GAME_DATE = "2025-06-19"
PLAYER_NAME = "Pascal Siakam"
TEAM_VS = "Oklahoma City Thunder"

# Function to make API requests
def make_request(url, use_proxy=False):
    endpoint = PROXY_ENDPOINT if use_proxy else PRIMARY_ENDPOINT
    full_url = f"{endpoint}{url}"
    try:
        response = requests.get(full_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        if use_proxy:
            print("Proxy failed, trying primary endpoint.")
            return make_request(url, use_proxy=False)
        else:
            print(f"HTTP Error: {e}")
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
    return None

# Function to find the game and check player's points
def check_player_points():
    games_today = make_request(f"/scores/json/GamesByDate/{GAME_DATE}")
    if not games_today:
        return "p4"  # Unable to retrieve data

    for game in games_today:
        if game['Status'] != "Final":
            continue
        if TEAM_VS in [game['HomeTeam'], game['AwayTeam']]:
            game_id = game['GameID']
            player_stats = make_request(f"/stats/json/PlayerGameStatsByGame/{game_id}")
            if player_stats:
                for player in player_stats:
                    if player['Name'] == PLAYER_NAME:
                        points = player['Points']
                        if points > 22.5:
                            return "p2"  # Yes, scored more than 22.5 points
                        else:
                            return "p1"  # No, did not score more than 22.5 points
            return "p1"  # Player did not play or no points data available

    return "p1"  # Game not found or not completed

# Main execution
if __name__ == "__main__":
    result = check_player_points()
    print(f"recommendation: {result}")