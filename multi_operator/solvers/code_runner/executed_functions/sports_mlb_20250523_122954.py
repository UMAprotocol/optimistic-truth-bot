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

# Function to make API requests
def make_request(endpoint, path):
    url = f"{endpoint}{path}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if endpoint == PROXY_ENDPOINT:
            print("Proxy failed, trying primary endpoint")
            return make_request(PRIMARY_ENDPOINT, path)
        else:
            print(f"Error: {e}")
            return None

# Function to check Anthony Edwards' points
def check_anthony_edwards_points():
    date_of_game = "2025-05-22"
    games_today = make_request(PROXY_ENDPOINT, f"/scores/json/GamesByDate/{date_of_game}")

    if not games_today:
        return "recommendation: p1"  # Resolve to "No" if API fails or no data

    for game in games_today:
        if game['Status'] != 'Final':
            continue
        if 'Minnesota Timberwolves' in [game['HomeTeam'], game['AwayTeam']] and 'Oklahoma City Thunder' in [game['HomeTeam'], game['AwayTeam']]:
            game_id = game['GameID']
            player_stats = make_request(PROXY_ENDPOINT, f"/stats/json/PlayerGameStatsByGame/{game_id}")
            if player_stats:
                for player in player_stats:
                    if player['Name'] == 'Anthony Edwards' and player['Points'] >= 25:
                        return "recommendation: p2"  # Yes, he scored 25+ points
            return "recommendation: p1"  # No, he did not score 25+ points

    return "recommendation: p1"  # Default to "No" if game not found or other conditions

# Main execution
if __name__ == "__main__":
    result = check_anthony_edwards_points()
    print(result)