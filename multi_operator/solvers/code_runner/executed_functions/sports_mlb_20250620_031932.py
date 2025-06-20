import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NBA_API_KEY")

# Configuration
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
GAME_DATE = "2025-06-19"
PLAYER_NAME = "Pascal Siakam"
TEAM_VS = "Oklahoma City Thunder"

# URL Endpoints
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nba"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-nba-proxy"

# Function to make API requests
def make_request(url, headers):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error during API request: {e}")
        return None

# Function to find the game and check player's points
def check_player_points():
    # Construct the URL for games on the specific date
    date_formatted = datetime.strptime(GAME_DATE, "%Y-%m-%d").strftime("%Y-%b-%d")
    games_url = f"{PROXY_ENDPOINT}/scores/json/GamesByDate/{date_formatted}"

    # Make the request to the proxy endpoint
    games = make_request(games_url, HEADERS)
    if not games:  # Fallback to primary if proxy fails
        games_url = f"{PRIMARY_ENDPOINT}/scores/json/GamesByDate/{date_formatted}"
        games = make_request(games_url, HEADERS)

    if games is None:
        return "recommendation: p3"  # Unknown/50-50 if API fails

    # Find the specific game
    for game in games:
        if game['Status'] == 'Scheduled' and TEAM_VS in [game['HomeTeam'], game['AwayTeam']]:
            # Check if the game is postponed or cancelled
            if game['Status'] not in ['Final', 'InProgress']:
                return "recommendation: p1"  # Resolve to "No" if not played

            # Get game ID and check player stats
            game_id = game['GameID']
            player_stats_url = f"{PRIMARY_ENDPOINT}/stats/json/PlayerGameStatsByGame/{game_id}"
            player_stats = make_request(player_stats_url, HEADERS)

            if player_stats is None:
                return "recommendation: p3"  # Unknown/50-50 if API fails

            # Check points scored by Pascal Siakam
            for player_stat in player_stats:
                if player_stat['Name'] == PLAYER_NAME:
                    points = player_stat['Points']
                    return "recommendation: p2" if points > 22.5 else "recommendation: p1"

    return "recommendation: p1"  # Resolve to "No" if no matching game or player not found

# Main execution
if __name__ == "__main__":
    result = check_player_points()
    print(result)