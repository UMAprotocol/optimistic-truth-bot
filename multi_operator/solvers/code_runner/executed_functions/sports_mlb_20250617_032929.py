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
            print(f"Failed to retrieve data: {e}")
            return None

# Function to check if any player scored 40+ points
def check_high_scores():
    current_year = datetime.now().year
    games = make_request(PROXY_ENDPOINT, f"/scores/json/Games/{current_year}")

    if games is None:
        return "p4"  # Unable to retrieve data

    for game in games:
        if '2025' in game['Day'] and (game['AwayTeam'] == 'OKC' and game['HomeTeam'] == 'IND') or (game['AwayTeam'] == 'IND' and game['HomeTeam'] == 'OKC'):
            game_id = game['GameID']
            stats = make_request(PROXY_ENDPOINT, f"/stats/json/PlayerGameStatsByGame/{game_id}")
            if stats:
                for player in stats:
                    if player['Points'] > 39.5:
                        return "p2"  # Yes, a player scored 40+ points

    return "p1"  # No player scored 40+ points

# Main execution
if __name__ == "__main__":
    result = check_high_scores()
    print(f"recommendation: {result}")