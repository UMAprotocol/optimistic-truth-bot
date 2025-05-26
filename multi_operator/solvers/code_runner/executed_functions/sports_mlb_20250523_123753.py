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

# Function to handle API requests
def get_data(url, use_proxy=False):
    endpoint = PROXY_ENDPOINT if use_proxy else PRIMARY_ENDPOINT
    full_url = f"{endpoint}{url}"
    try:
        response = requests.get(full_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if use_proxy:
            print("Proxy failed, trying primary endpoint.")
            return get_data(url, use_proxy=False)
        else:
            print(f"Failed to retrieve data: {e}")
            return None

# Function to check game and player performance
def check_game_and_performance(date, team, player):
    games = get_data(f"/scores/json/GamesByDate/{date}")
    if games:
        for game in games:
            if team in (game['HomeTeam'], game['AwayTeam']):
                if game['Status'] == "Final":
                    player_stats = get_data(f"/stats/json/PlayerGameStatsByDate/{date}")
                    if player_stats:
                        for stat in player_stats:
                            if stat['Name'] == player and stat['Team'] == team:
                                points = stat['Points']
                                if points > 24.5:
                                    return "p2"  # Yes, conditions met
                                else:
                                    return "p1"  # No, player did not score enough
                else:
                    return "p1"  # No, game not completed or postponed
    return "p1"  # No, game not found or other issues

# Main execution function
def main():
    date = "2025-05-22"
    team = "MIN"  # Minnesota Timberwolves
    player = "Anthony Edwards"
    result = check_game_and_performance(date, team, player)
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()