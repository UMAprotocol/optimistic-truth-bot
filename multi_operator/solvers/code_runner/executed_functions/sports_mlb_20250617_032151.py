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

# Date and team information
GAME_DATE = "2025-06-16"
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
    except requests.RequestException as e:
        if use_proxy:
            print("Proxy failed, trying primary endpoint.")
            return make_request(url, use_proxy=False)
        else:
            print(f"Failed to retrieve data: {e}")
            return None

# Function to find the game and check player's points
def check_player_performance():
    date_formatted = datetime.strptime(GAME_DATE, "%Y-%m-%d").strftime("%Y-%m-%d")
    games = make_request(f"/scores/json/GamesByDate/{date_formatted}", use_proxy=True)
    if not games:
        return "p4"  # Unable to retrieve data

    for game in games:
        if game['Status'] == "Scheduled":
            continue
        if TEAM_VS in [game['HomeTeam'], game['AwayTeam']]:
            game_id = game['GameID']
            player_stats = make_request(f"/stats/json/PlayerGameStatsByGame/{game_id}", use_proxy=True)
            if player_stats:
                for stat in player_stats:
                    if stat['Name'] == PLAYER_NAME:
                        points = stat['Points']
                        if points > 16.5:
                            return "p2"  # Yes, scored more than 16.5 points
                        else:
                            return "p1"  # No, did not score more than 16.5 points
            return "p1"  # Player did not play or no points data available

    return "p4"  # Game not found or data not available

# Main execution
if __name__ == "__main__":
    result = check_player_performance()
    print(f"recommendation: {result}")