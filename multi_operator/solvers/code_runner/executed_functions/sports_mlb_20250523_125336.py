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
GAME_DATE = "2025-05-22"
PLAYER_NAME = "Shai Gilgeous-Alexander"
TEAM_ABBREVIATION = "OKC"  # Oklahoma City Thunder
OPPONENT_ABBREVIATION = "MIN"  # Minnesota Timberwolves

# API Endpoints
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nba"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/nba-proxy"

# Function to make API requests
def make_request(endpoint, path):
    url = f"{endpoint}{path}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error accessing {url}: {str(e)}")
        return None

# Function to find the game and check player's points
def check_player_performance():
    date_formatted = datetime.strptime(GAME_DATE, "%Y-%m-%d").strftime("%Y-%b-%d")
    games_path = f"/scores/json/GamesByDate/{date_formatted}"

    # Try proxy first
    games = make_request(PROXY_ENDPOINT, games_path)
    if not games:
        # Fallback to primary if proxy fails
        games = make_request(PRIMARY_ENDPOINT, games_path)
        if not games:
            return "p4"  # Unable to retrieve data

    # Find the specific game
    for game in games:
        if {game["HomeTeam"], game["AwayTeam"]} == {TEAM_ABBREVIATION, OPPONENT_ABBREVIATION}:
            if game["Status"] != "Final":
                return "p1"  # Game not completed or player did not play
            # Check player's performance
            player_stats_path = f"/stats/json/PlayerGameStatsByGame/{game['GameID']}"
            player_stats = make_request(PRIMARY_ENDPOINT, player_stats_path)
            if player_stats:
                for stat in player_stats:
                    if stat["Name"] == PLAYER_NAME:
                        points = stat.get("Points", 0)
                        return "p2" if points > 30.5 else "p1"
            return "p1"  # Player did not play or data not available
    return "p1"  # Game not found or postponed

# Main execution
if __name__ == "__main__":
    result = check_player_performance()
    print(f"recommendation: {result}")