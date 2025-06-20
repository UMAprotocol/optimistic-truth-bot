import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
NBA_API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")
if not NBA_API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NBA_API_KEY")

# Configuration for API requests
HEADERS = {"Ocp-Apim-Subscription-Key": NBA_API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nba"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

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

# Function to check if any player scored 40+ points
def check_high_scores():
    current_year = datetime.now().year
    games = make_request(f"/scores/json/Games/{current_year}", use_proxy=True)
    if games:
        for game in games:
            if 'Oklahoma City Thunder' in game['HomeTeam'] or 'Oklahoma City Thunder' in game['AwayTeam']:
                if 'Indiana Pacers' in game['HomeTeam'] or 'Indiana Pacers' in game['AwayTeam']:
                    game_id = game['GameID']
                    stats = make_request(f"/stats/json/PlayerGameStatsByGame/{game_id}", use_proxy=True)
                    if stats:
                        for player in stats:
                            if player['Points'] > 39.5:
                                return True
    return False

# Main function to determine the market resolution
def resolve_market():
    if check_high_scores():
        print("recommendation: p2")  # Yes, a player scored 40+ points
    else:
        print("recommendation: p1")  # No player scored 40+ points

# Run the resolution function
if __name__ == "__main__":
    resolve_market()