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
            print(f"Failed to retrieve data: {e}")
            return None

# Function to check Anthony Edwards' score
def check_anthony_edwards_score():
    date_of_game = "2025-05-28"
    player_name = "Anthony Edwards"
    team = "Minnesota Timberwolves"
    opponent = "Oklahoma City Thunder"

    # Fetch games by date
    games = make_request(PROXY_ENDPOINT, f"/scores/json/GamesByDate/{date_of_game}")
    if not games:
        return "recommendation: p1"  # Resolve to "No" if no data available

    # Find the specific game
    game_id = None
    for game in games:
        if game['HomeTeam'] == team or game['AwayTeam'] == team:
            if game['HomeTeam'] == opponent or game['AwayTeam'] == opponent:
                game_id = game['GameID']
                break

    if not game_id:
        return "recommendation: p1"  # Resolve to "No" if game not found

    # Fetch player game stats by game ID
    player_stats = make_request(PROXY_ENDPOINT, f"/stats/json/PlayerGameStatsByGame/{game_id}")
    if not player_stats:
        return "recommendation: p1"  # Resolve to "No" if no player stats available

    # Check Anthony Edwards' score
    for stat in player_stats:
        if stat['Name'] == player_name:
            points = stat['Points']
            if points > 27.5:
                return "recommendation: p2"  # Resolve to "Yes"
            else:
                return "recommendation: p1"  # Resolve to "No"

    return "recommendation: p1"  # Resolve to "No" if Anthony Edwards did not play

# Main execution
if __name__ == "__main__":
    result = check_anthony_edwards_score()
    print(result)