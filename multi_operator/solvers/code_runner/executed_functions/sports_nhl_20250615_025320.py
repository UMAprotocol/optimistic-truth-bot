import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NHL_API_KEY")

# Configuration for API requests
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nhl"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-nhl-proxy"

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

# Function to check if Barkov scored in the game
def check_barkov_score(game_id):
    game_boxscore = make_request(f"/scores/json/BoxScore/{game_id}")
    if game_boxscore:
        for player in game_boxscore['PlayerGames']:
            if player['Name'] == "Aleksander Barkov" and player['Goals'] > 0:
                return True
    return False

# Main function to resolve the market
def resolve_market():
    today = datetime.now()
    game_date = datetime(2025, 6, 14, 20)  # Game date and time in ET
    if today < game_date:
        return "recommendation: p4"  # Game has not occurred yet
    elif today.year > 2025 or (today.year == 2025 and today.month > 12):
        return "recommendation: p3"  # Past the resolution date without a game

    # Fetch games on the specific date
    games_on_date = make_request(f"/scores/json/GamesByDate/{game_date.strftime('%Y-%m-%d')}")
    if games_on_date:
        for game in games_on_date:
            if game['AwayTeam'] == "FLA" and game['HomeTeam'] == "EDM":
                if check_barkov_score(game['GameID']):
                    return "recommendation: p2"  # Barkov scored
                else:
                    return "recommendation: p1"  # Barkov did not score

    return "recommendation: p3"  # Game not found or no score data available

# Execute the main function
if __name__ == "__main__":
    result = resolve_market()
    print(result)