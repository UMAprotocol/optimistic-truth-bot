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
        print(f"Error: {e}")
        return None

# Function to check Shai Gilgeous-Alexander's points
def check_points():
    date_of_game = "2025-05-22"
    player_name = "Shai Gilgeous-Alexander"
    team = "Oklahoma City Thunder"
    opponent = "Minnesota Timberwolves"

    # Try proxy endpoint first
    games = make_request(PROXY_ENDPOINT, f"/scores/json/GamesByDate/{date_of_game}")
    if not games:
        # Fallback to primary endpoint
        games = make_request(PRIMARY_ENDPOINT, f"/scores/json/GamesByDate/{date_of_game}")

    if games:
        for game in games:
            if game['HomeTeam'] == team or game['AwayTeam'] == team:
                if game['HomeTeam'] == opponent or game['AwayTeam'] == opponent:
                    game_id = game['GameID']
                    stats = make_request(PRIMARY_ENDPOINT, f"/stats/json/PlayerGameStatsByGame/{game_id}")
                    if stats:
                        for stat in stats:
                            if stat['Name'] == player_name:
                                points = stat['Points']
                                if points > 30.5:
                                    return "recommendation: p2"  # Yes
                                else:
                                    return "recommendation: p1"  # No
    return "recommendation: p1"  # No, if game not found or player did not play

# Main execution
if __name__ == "__main__":
    result = check_points()
    print(result)