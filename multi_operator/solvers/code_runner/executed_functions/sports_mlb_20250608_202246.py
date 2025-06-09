import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# Configuration for headers and endpoints
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/mlb/scores/json"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/mlb-proxy"

# Function to make API requests
def make_request(url, use_proxy=False):
    endpoint = PROXY_ENDPOINT if use_proxy else PRIMARY_ENDPOINT
    full_url = f"{endpoint}{url}"
    try:
        response = requests.get(full_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        if use_proxy:
            print("Proxy failed, trying primary endpoint.")
            return make_request(url, use_proxy=False)
        else:
            print(f"HTTP Error: {e}")
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
    return None

# Function to check if Ronaldo scored in the game
def check_ronaldo_score():
    date_of_game = "2025-06-08"
    games = make_request(f"/GamesByDate/{date_of_game}")
    if games is None:
        return "p3"  # Unknown or API failure

    for game in games:
        if game['Status'] == 'Final' and {'Portugal', 'Spain'} == {game['HomeTeam'], game['AwayTeam']}:
            # Check player stats
            game_id = game['GameID']
            player_stats = make_request(f"/PlayerGameStatsByGame/{game_id}")
            if player_stats is None:
                return "p3"  # Unknown or API failure

            for player in player_stats:
                if player['Name'] == 'Cristiano Ronaldo' and player['Goals'] > 0:
                    return "p2"  # Ronaldo scored
            return "p1"  # Ronaldo did not score

    return "p3"  # Game not found or not final

# Main execution
if __name__ == "__main__":
    result = check_ronaldo_score()
    print(f"recommendation: {result}")