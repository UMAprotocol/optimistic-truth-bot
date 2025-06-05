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
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

# Function to handle requests with a fallback mechanism
def make_request(url, params=None):
    try:
        # Try proxy endpoint first
        response = requests.get(f"{PROXY_ENDPOINT}{url}", headers=HEADERS, params=params, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            # Fallback to primary endpoint if proxy fails
            response = requests.get(f"{PRIMARY_ENDPOINT}{url}", headers=HEADERS, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
    except requests.RequestException as e:
        print(f"Error during requests to {url}: {str(e)}")
        return None

# Function to check if Hakimi Achraf scored in the game
def check_hakimi_score(game_id):
    game_boxscore = make_request(f"/Boxscore/{game_id}")
    if game_boxscore:
        for player in game_boxscore.get('PlayerGames', []):
            if player.get('Name') == "Hakimi Achraf" and player.get('Scoring', {}).get('Goals', 0) > 0.5:
                return True
    return False

# Main function to resolve the market
def resolve_market():
    # Define the date of the Champions League final
    final_date = "2025-05-31"
    # Fetch games on the final date
    games_on_date = make_request(f"/GamesByDate/{final_date}")
    if not games_on_date:
        print("No games found or error fetching games.")
        return "recommendation: p4"

    # Find the specific game
    for game in games_on_date:
        if game['HomeTeam'] == "Paris Saint-Germain" and game['AwayTeam'] == "Inter Milan":
            if datetime.now() < datetime(2025, 12, 31, 23, 59):
                if check_hakimi_score(game['GameID']):
                    return "recommendation: p2"  # Hakimi scored
                else:
                    return "recommendation: p1"  # Hakimi did not score
            else:
                return "recommendation: p3"  # Market resolves to 50-50 after 2025-12-31

    # If no specific game is found or it's too early to resolve
    return "recommendation: p4"

# Run the main function
if __name__ == "__main__":
    result = resolve_market()
    print(result)