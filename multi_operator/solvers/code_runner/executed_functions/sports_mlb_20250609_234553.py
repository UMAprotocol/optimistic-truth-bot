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
GAME_DATE = "2025-05-29"
TEAM = "Indiana Pacers"
PLAYER = "Tyrese Haliburton"
POINTS_THRESHOLD = 22.5

# NBA API endpoints
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nba"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/nba-proxy"

# Function to make API requests
def make_request(url, headers):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

# Function to find the game and check conditions
def check_game_and_player_performance():
    date_formatted = datetime.strptime(GAME_DATE, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = f"{PRIMARY_ENDPOINT}/scores/json/GamesByDate/{date_formatted}"
    
    games = make_request(url, HEADERS)
    if not games:
        print("Failed to retrieve games data. Trying proxy...")
        games = make_request(PROXY_ENDPOINT + url, HEADERS)
        if not games:
            return "recommendation: p1"  # Resolve to "No" if data cannot be retrieved

    for game in games:
        if TEAM in (game['HomeTeam'], game['AwayTeam']):
            if game['Status'] != "Final":
                return "recommendation: p1"  # Game not completed or postponed

            # Check player performance
            game_id = game['GameID']
            player_stats_url = f"{PRIMARY_ENDPOINT}/stats/json/PlayerGameStatsByGame/{game_id}"
            player_stats = make_request(player_stats_url, HEADERS)
            if not player_stats:
                print("Failed to retrieve player stats. Trying proxy...")
                player_stats = make_request(PROXY_ENDPOINT + player_stats_url, HEADERS)
                if not player_stats:
                    return "recommendation: p1"  # Resolve to "No" if data cannot be retrieved

            for player in player_stats:
                if player['Name'] == PLAYER and player['Points'] > POINTS_THRESHOLD:
                    if game['HomeTeam'] == TEAM and game['HomeTeamScore'] > game['AwayTeamScore']:
                        return "recommendation: p2"  # Yes, conditions met
                    elif game['AwayTeam'] == TEAM and game['AwayTeamScore'] > game['HomeTeamScore']:
                        return "recommendation: p2"  # Yes, conditions met
            return "recommendation: p1"  # Player did not meet points condition or team did not win

    return "recommendation: p1"  # No relevant game found or conditions not met

# Main execution
if __name__ == "__main__":
    result = check_game_and_player_performance()
    print(result)