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
def make_request(endpoint, path, use_proxy=False):
    url = f"{PROXY_ENDPOINT if use_proxy else PRIMARY_ENDPOINT}{path}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if use_proxy:
            print("Proxy failed, trying primary endpoint.")
            return make_request(endpoint, path, use_proxy=False)
        else:
            print(f"Failed to retrieve data: {e}")
            return None

# Function to check game outcome and player performance
def check_game_and_performance(date, team, player):
    games_today = make_request(PRIMARY_ENDPOINT, f"/scores/json/GamesByDate/{date}", use_proxy=True)
    if games_today:
        for game in games_today:
            if game['Status'] == 'Final' and (game['HomeTeam'] == team or game['AwayTeam'] == team):
                game_id = game['GameID']
                stats = make_request(PRIMARY_ENDPOINT, f"/stats/json/PlayerGameStatsByGame/{game_id}", use_proxy=True)
                if stats:
                    for stat in stats:
                        if stat['Name'] == player and stat['Points'] > 29.5:
                            if (game['HomeTeam'] == team and game['HomeTeamScore'] > game['AwayTeamScore']) or \
                               (game['AwayTeam'] == team and game['AwayTeamScore'] > game['HomeTeamScore']):
                                return "p2"  # Knicks win and Brunson scores 30+ points
    return "p1"  # Either Knicks didn't win or Brunson didn't score 30+ points

# Main function to run the check
def main():
    date = "2025-05-23"
    team = "New York Knicks"
    player = "Jalen Brunson"
    result = check_game_and_performance(date, team, player)
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()