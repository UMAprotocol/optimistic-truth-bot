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

# Function to check game result and player performance
def check_game_and_performance(date, team, player):
    # Format date for API request
    formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m-%d")
    games_today = make_request(PROXY_ENDPOINT, f"/scores/json/GamesByDate/{formatted_date}")

    if not games_today:
        return "p4"  # Unable to retrieve data

    # Find the specific game
    for game in games_today:
        if team in [game['HomeTeam'], game['AwayTeam']]:
            if game['Status'] != "Final":
                return "p1"  # Game not completed or postponed
            # Check game outcome
            team_won = (game['Winner'] == team)
            # Check player performance
            player_stats = make_request(PROXY_ENDPOINT, f"/stats/json/PlayerGameStatsByDate/{formatted_date}/{player}")
            if not player_stats:
                return "p4"  # Unable to retrieve player stats
            player_scored_25_plus = any(ps['Points'] > 24.5 for ps in player_stats if ps['Name'] == player)
            # Determine final outcome
            if team_won and player_scored_25_plus:
                return "p2"
            else:
                return "p1"
    return "p1"  # Game not found or conditions not met

# Main execution function
def main():
    # Hardcoded values from the question
    game_date = "2025-05-22"
    team = "Minnesota Timberwolves"
    player = "Anthony Edwards"
    result = check_game_and_performance(game_date, team, player)
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()