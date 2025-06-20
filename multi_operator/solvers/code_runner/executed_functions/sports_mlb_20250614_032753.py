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
GAME_DATE = "2025-06-13"
PLAYER_NAME = "Shai Gilgeous-Alexander"
TEAM = "Oklahoma City Thunder"
OPPONENT_TEAM = "Indiana Pacers"

# URL configurations
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nba"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-nba-proxy"

# Function to make API requests
def make_request(url, headers):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error during request: {e}")
        return None

# Function to find the game and check player's score
def check_player_score(game_date, player_name, team, opponent_team):
    formatted_date = datetime.strptime(game_date, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = f"{PROXY_ENDPOINT}/scores/json/GamesByDate/{formatted_date}"
    games = make_request(url, HEADERS)
    if not games:
        print("Switching to primary endpoint due to proxy failure.")
        url = f"{PRIMARY_ENDPOINT}/scores/json/GamesByDate/{formatted_date}"
        games = make_request(url, HEADERS)

    if games:
        for game in games:
            if (game['HomeTeam'] == team or game['AwayTeam'] == team) and \
               (game['HomeTeam'] == opponent_team or game['AwayTeam'] == opponent_team):
                game_id = game['GameID']
                player_stats_url = f"{PRIMARY_ENDPOINT}/stats/json/PlayerGameStatsByGame/{game_id}"
                player_stats = make_request(player_stats_url, HEADERS)
                if player_stats:
                    for stat in player_stats:
                        if stat['Name'] == player_name:
                            points = stat['Points']
                            return points >= 34
    return False

# Main execution
if __name__ == "__main__":
    result = check_player_score(GAME_DATE, PLAYER_NAME, TEAM, OPPONENT_TEAM)
    recommendation = "p2" if result else "p1"
    print(f"recommendation: {recommendation}")