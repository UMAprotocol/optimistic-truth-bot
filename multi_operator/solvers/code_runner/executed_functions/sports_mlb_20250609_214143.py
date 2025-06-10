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
            print(f"Failed to retrieve data: {e}")
            return None

# Function to check game outcome and player performance
def check_game_and_performance(date, team, player):
    # Format date for API request
    formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m-%d")
    games_today = make_request(PROXY_ENDPOINT, f"/scores/json/GamesByDate/{formatted_date}")

    if not games_today:
        return "p1"  # Resolve to "No" if no data available

    for game in games_today:
        if game['Status'] != "Final":
            continue
        if team in [game['HomeTeam'], game['AwayTeam']]:
            if game['Winner'] == team:
                # Check player performance
                player_stats = make_request(PROXY_ENDPOINT, f"/stats/json/PlayerGameStatsByDate/{formatted_date}/{player}")
                if player_stats and any(ps['Points'] > 33.5 for ps in player_stats if ps['Name'] == player):
                    return "p2"  # Resolve to "Yes"
                else:
                    return "p1"  # Resolve to "No"
            else:
                return "p1"  # Resolve to "No"
    return "p1"  # Resolve to "No" if no matching game found

# Main execution function
if __name__ == "__main__":
    # Specific game and player details
    game_date = "2025-05-28"
    team_name = "Oklahoma City Thunder"
    player_name = "Shai Gilgeous-Alexander"

    # Print the recommendation based on the game and player performance
    recommendation = check_game_and_performance(game_date, team_name, player_name)
    print(f"recommendation: {recommendation}")