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
PLAYER_NAME = "Jalen Williams"
TEAM_NAME = "Oklahoma City Thunder"
OPPONENT_TEAM = "Indiana Pacers"

# API Endpoints
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nba"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-nba-proxy"

# Function to make API requests
def make_request(url, headers, use_proxy=False):
    try:
        response = requests.get(PROXY_ENDPOINT + url if use_proxy else url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if use_proxy:
            print("Proxy failed, trying primary endpoint.")
            return make_request(url, headers, use_proxy=False)
        else:
            print(f"Failed to retrieve data: {e}")
            return None

# Function to find the game and check player's score
def check_player_score(game_date, player_name, team_name, opponent_team):
    date_formatted = datetime.strptime(game_date, "%Y-%m-%d").strftime("%Y-%m-%d")
    games_url = f"{PRIMARY_ENDPOINT}/scores/json/GamesByDate/{date_formatted}"
    games_data = make_request(games_url, HEADERS)

    if games_data:
        for game in games_data:
            if (game['HomeTeam'] == team_name or game['AwayTeam'] == team_name) and \
               (game['HomeTeam'] == opponent_team or game['AwayTeam'] == opponent_team):
                game_id = game['GameID']
                stats_url = f"{PRIMARY_ENDPOINT}/stats/json/PlayerGameStatsByGame/{game_id}"
                stats_data = make_request(stats_url, HEADERS)
                if stats_data:
                    for stat in stats_data:
                        if stat['Name'] == player_name:
                            points = stat['Points']
                            return points >= 25.5
    return False

# Main execution
if __name__ == "__main__":
    result = check_player_score(GAME_DATE, PLAYER_NAME, TEAM_NAME, OPPONENT_TEAM)
    recommendation = "p2" if result else "p1"
    print(f"recommendation: {recommendation}")