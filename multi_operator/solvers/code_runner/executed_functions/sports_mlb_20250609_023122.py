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
GAME_DATE = "2025-06-08"
PLAYER_NAME = "Shai Gilgeous-Alexander"
TEAM = "Oklahoma City Thunder"
OPPONENT_TEAM = "Indiana Pacers"
POINTS_THRESHOLD = 33.5

# Resolution map
RESOLUTION_MAP = {
    "Yes": "p2",
    "No": "p1",
    "Unknown": "p3"
}

# API Endpoints
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nba"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/nba-proxy"

# Function to make API requests
def make_request(url, headers):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error during API request: {e}")
        return None

# Function to check player's points
def check_player_points(game_date, player_name, team, opponent_team, points_threshold):
    date_formatted = datetime.strptime(game_date, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = f"{PROXY_ENDPOINT}/scores/json/GamesByDate/{date_formatted}"
    games = make_request(url, HEADERS)
    if not games:
        url = f"{PRIMARY_ENDPOINT}/scores/json/GamesByDate/{date_formatted}"
        games = make_request(url, HEADERS)
        if not games:
            return RESOLUTION_MAP["Unknown"]

    for game in games:
        if game['HomeTeam'] == team and game['AwayTeam'] == opponent_team:
            if game['Status'] != "Final":
                return RESOLUTION_MAP["No"]
            player_stats_url = f"{PRIMARY_ENDPOINT}/stats/json/PlayerGameStatsByGame/{game['GameID']}"
            player_stats = make_request(player_stats_url, HEADERS)
            if player_stats:
                for stat in player_stats:
                    if stat['Name'] == player_name:
                        points = stat['Points']
                        return RESOLUTION_MAP["Yes"] if points > points_threshold else RESOLUTION_MAP["No"]
    return RESOLUTION_MAP["No"]

# Main execution
if __name__ == "__main__":
    result = check_player_points(GAME_DATE, PLAYER_NAME, TEAM, OPPONENT_TEAM, POINTS_THRESHOLD)
    print(f"recommendation: {result}")