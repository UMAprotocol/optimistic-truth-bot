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
            print("Proxy failed, trying primary endpoint.")
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
            if game['Status'] == 'Final' and (game['HomeTeam'] == team or game['AwayTeam'] == team):
                game_id = game['GameID']
                stats = make_request(PROXY_ENDPOINT, f"/stats/json/PlayerGameStatsByGame/{game_id}")
                if stats:
                    for stat in stats:
                        if stat['Name'] == player and stat['Team'] == team:
                            points = stat['Points']
                            if points > 34.5 and game['Winner'] == team:
                                return "p2"  # Thunder win and SGA scores 35+ points
    return "p1"  # Other outcomes

# Main execution function
if __name__ == "__main__":
    # Specific game details
    game_date = "2025-06-11"
    team_name = "Oklahoma City Thunder"
    player_name = "Shai Gilgeous-Alexander"

    # Check the game outcome and player performance
    result = check_game_and_performance(game_date, team_name, player_name)
    print(f"recommendation: {result}")