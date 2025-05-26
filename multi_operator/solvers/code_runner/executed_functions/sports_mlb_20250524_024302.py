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
        if endpoint == PROXY_ENDPOINT:
            print("Proxy failed, trying primary endpoint")
            return make_request(PRIMARY_ENDPOINT, path)
        else:
            print(f"Error: {e}")
            return None

# Function to check game outcome and player performance
def check_game_and_performance(date, team, player_name, points_threshold):
    # Format date for API request
    formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m-%d")
    games_today = make_request(PROXY_ENDPOINT, f"/scores/json/GamesByDate/{formatted_date}")

    if not games_today:
        return "p1"  # No data available, resolve as "No"

    # Find the specific game
    for game in games_today:
        if team in (game['HomeTeam'], game['AwayTeam']):
            if game['Status'] != "Final":
                return "p1"  # Game not completed, resolve as "No"
            # Check game outcome
            winning_team = game['HomeTeam'] if game['HomeTeamScore'] > game['AwayTeamScore'] else game['AwayTeam']
            if winning_team != team:
                return "p1"  # Team did not win, resolve as "No"

            # Check player performance
            game_id = game['GameID']
            player_stats = make_request(PROXY_ENDPOINT, f"/stats/json/PlayerGameStatsByGame/{game_id}")
            for player in player_stats:
                if player['Name'] == player_name and player['Points'] > points_threshold:
                    return "p2"  # Both conditions met, resolve as "Yes"
            return "p1"  # Player did not score enough points, resolve as "No"
    return "p1"  # Game not found, resolve as "No"

# Main execution
if __name__ == "__main__":
    result = check_game_and_performance("2025-05-23", "IND", "Tyrese Haliburton", 20.5)
    print(f"recommendation: {result}")