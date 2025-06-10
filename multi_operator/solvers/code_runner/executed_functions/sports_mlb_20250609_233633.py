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

# Game and player details
GAME_DATE = "2025-05-29"
TEAM_NAME = "New York Knicks"
PLAYER_NAME = "Jalen Brunson"
SCORE_THRESHOLD = 30.5

# Function to make API requests
def make_request(url, use_proxy=False):
    endpoint = PROXY_ENDPOINT if use_proxy else PRIMARY_ENDPOINT
    full_url = f"{endpoint}{url}"
    try:
        response = requests.get(full_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if use_proxy:
            print("Proxy failed, trying primary endpoint.")
            return make_request(url, use_proxy=False)
        else:
            print(f"Failed to retrieve data: {e}")
            return None

# Function to find the game and check the conditions
def check_game_and_player_performance():
    # Format the date for the API request
    formatted_date = datetime.strptime(GAME_DATE, "%Y-%m-%d").strftime("%Y-%m-%d")
    games = make_request(f"/scores/json/GamesByDate/{formatted_date}", use_proxy=True)
    
    if not games:
        return "recommendation: p1"  # Resolve to "No" if no data is available

    # Find the specific game
    for game in games:
        if TEAM_NAME in (game['HomeTeam'], game['AwayTeam']):
            if game['Status'] != "Final":
                return "recommendation: p1"  # Game not completed or cancelled/postponed

            # Check player performance if the Knicks won
            if (game['HomeTeam'] == TEAM_NAME and game['HomeTeamScore'] > game['AwayTeamScore']) or \
               (game['AwayTeam'] == TEAM_NAME and game['AwayTeamScore'] > game['HomeTeamScore']):
                # Retrieve player stats
                player_stats = make_request(f"/stats/json/PlayerGameStatsByDate/{formatted_date}", use_proxy=True)
                if player_stats:
                    for stat in player_stats:
                        if stat['Name'] == PLAYER_NAME and stat['Points'] > SCORE_THRESHOLD:
                            return "recommendation: p2"  # Knicks won and Brunson scored over 30.5 points
                return "recommendation: p1"  # Player did not meet the scoring threshold
            else:
                return "recommendation: p1"  # Knicks did not win
    return "recommendation: p1"  # Game not found or conditions not met

# Main execution
if __name__ == "__main__":
    result = check_game_and_player_performance()
    print(result)