import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NBA_API_KEY")

# Configuration for headers and API endpoints
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nba"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-nba-proxy"

# Function to make API requests
def make_request(endpoint, path):
    url = f"{endpoint}{path}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if endpoint == PROXY_ENDPOINT:
            print(f"Falling back to primary endpoint due to error: {e}")
            return make_request(PRIMARY_ENDPOINT, path)
        else:
            print(f"Error accessing API: {e}")
            return None

# Function to check player's score
def check_player_score(game_date, player_name):
    formatted_date = datetime.strptime(game_date, "%Y-%m-%d").strftime("%Y-%m-%d")
    games_path = f"/scores/json/GamesByDate/{formatted_date}"
    games_data = make_request(PROXY_ENDPOINT, games_path)

    if games_data:
        for game in games_data:
            if game['Status'] == 'Final':
                player_stats_path = f"/stats/json/PlayerGameStatsByDate/{formatted_date}"
                player_stats = make_request(PROXY_ENDPOINT, player_stats_path)
                if player_stats:
                    for stat in player_stats:
                        if stat['Name'] == player_name and stat['Team'] in [game['HomeTeam'], game['AwayTeam']]:
                            points = stat.get('Points', 0)
                            return points
    return None

# Main function to resolve the market
def resolve_market():
    game_date = "2025-06-13"
    player_name = "Shai Gilgeous-Alexander"
    points_needed = 34

    score = check_player_score(game_date, player_name)
    if score is None:
        print("recommendation: p1")  # No data or game not final
    elif score >= points_needed:
        print("recommendation: p2")  # Player scored 34 or more points
    else:
        print("recommendation: p1")  # Player scored less than 34 points

# Run the main function
if __name__ == "__main__":
    resolve_market()