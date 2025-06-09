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

# URL configurations
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

# Function to find the game and check player's points
def check_player_performance(date, player_name, team, opponent_team):
    formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = f"{PRIMARY_ENDPOINT}/scores/json/GamesByDate/{formatted_date}"
    
    # Try proxy endpoint first
    games = make_request(PROXY_ENDPOINT + url, HEADERS)
    if not games:
        # Fallback to primary endpoint if proxy fails
        games = make_request(url, HEADERS)
    
    if games:
        for game in games:
            if (game['HomeTeam'] == team or game['AwayTeam'] == team) and \
               (game['HomeTeam'] == opponent_team or game['AwayTeam'] == opponent_team):
                # Check if the game is final
                if game['Status'] != "Final":
                    return "p4"  # Game not completed
                # Find player stats
                game_id = game['GameID']
                stats_url = f"{PRIMARY_ENDPOINT}/stats/json/PlayerGameStatsByGame/{game_id}"
                player_stats = make_request(PROXY_ENDPOINT + stats_url, HEADERS)
                if not player_stats:
                    player_stats = make_request(stats_url, HEADERS)
                if player_stats:
                    for stat in player_stats:
                        if stat['Name'] == player_name:
                            points = stat['Points']
                            return "p2" if points > POINTS_THRESHOLD else "p1"
    return "p1"  # Default to "No" if game is canceled, postponed, or player did not play

# Main execution
if __name__ == "__main__":
    result = check_player_performance(GAME_DATE, PLAYER_NAME, TEAM, OPPONENT_TEAM)
    print(f"recommendation: {result}")