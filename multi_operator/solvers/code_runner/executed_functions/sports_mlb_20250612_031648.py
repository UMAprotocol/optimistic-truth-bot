import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NBA_API_KEY")

# Configuration for headers and API endpoints
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
            print(f"Error: {e}")
            return None

# Function to check game outcome and player performance
def check_game_and_performance(date, team, player):
    # Format date for API request
    formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m-%d")
    games_today = make_request(PROXY_ENDPOINT, f"/scores/json/GamesByDate/{formatted_date}")

    if games_today:
        for game in games_today:
            if game['HomeTeam'] == team or game['AwayTeam'] == team:
                if game['Status'] != "Final":
                    return "p4"  # Game not completed
                # Check player performance
                player_stats = make_request(PROXY_ENDPOINT, f"/stats/json/PlayerGameStatsByDate/{formatted_date}/{player}")
                if player_stats:
                    for stat in player_stats:
                        if stat['Name'] == player and stat['Points'] > 34.5:
                            if (game['HomeTeam'] == team and game['HomeTeamScore'] > game['AwayTeamScore']) or \
                               (game['AwayTeam'] == team and game['AwayTeamScore'] > game['HomeTeamScore']):
                                return "p2"  # Team won and player scored over 34.5 points
                return "p1"  # Conditions not met
    return "p1"  # Game not found or other conditions not met

# Main execution function
if __name__ == "__main__":
    # Extracted information from the question
    game_date = "2025-06-11"
    team_name = "Oklahoma City Thunder"
    player_name = "Shai Gilgeous-Alexander"

    # Check the game outcome and player performance
    result = check_game_and_performance(game_date, team_name, player_name)
    print("recommendation:", result)