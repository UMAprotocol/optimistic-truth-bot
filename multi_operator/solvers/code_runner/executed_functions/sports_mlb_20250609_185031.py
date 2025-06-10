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

# Function to check player's score
def check_player_score(game_date, player_name):
    formatted_date = datetime.strptime(game_date, "%Y-%m-%d").strftime("%Y-%m-%d")
    games = make_request(PROXY_ENDPOINT, f"/scores/json/GamesByDate/{formatted_date}")
    if games:
        for game in games:
            if game['Status'] == 'Final':
                game_id = game['GameID']
                stats = make_request(PROXY_ENDPOINT, f"/stats/json/PlayerGameStatsByGame/{game_id}")
                if stats:
                    for stat in stats:
                        if stat['Name'] == player_name and stat['Points'] > 20.5:
                            return "p2"  # Yes, scored more than 20.5 points
    return "p1"  # No, did not score more than 20.5 points or game not final

# Main function to resolve the market
def resolve_market():
    game_date = "2025-05-31"
    player_name = "Tyrese Haliburton"
    result = check_player_score(game_date, player_name)
    print(f"recommendation: {result}")

# Run the main function
if __name__ == "__main__":
    resolve_market()