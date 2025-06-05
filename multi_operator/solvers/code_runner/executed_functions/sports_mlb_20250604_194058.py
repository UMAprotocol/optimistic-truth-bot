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
def make_request(endpoint, path):
    url = f"{endpoint}/{path}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if endpoint == PROXY_ENDPOINT:
            print(f"Falling back to primary endpoint due to error: {e}")
            return make_request(PRIMARY_ENDPOINT, path)
        else:
            print(f"Error accessing API: {e}")
            return None

# Function to check if Hakimi Achraf scored in the game
def check_hakimi_score(game_id):
    game_stats = make_request(PROXY_ENDPOINT, f"PlayerGameStatsByGame/{game_id}")
    if game_stats:
        for player_stat in game_stats:
            if player_stat['Name'] == "Hakimi Achraf" and player_stat['Scoring']['Goals'] > 0.5:
                return True
    return False

# Main function to resolve the market
def resolve_market():
    today = datetime.now()
    final_date = datetime(2025, 12, 31, 23, 59)
    if today > final_date:
        return "recommendation: p3"  # Market resolves to 50-50

    games_today = make_request(PROXY_ENDPOINT, "GamesByDate/2025-05-31")
    if games_today:
        for game in games_today:
            if game['HomeTeam'] == "Paris Saint-Germain" and game['AwayTeam'] == "Inter Milan":
                if game['Status'] == "Final":
                    if check_hakimi_score(game['GameID']):
                        return "recommendation: p2"  # Hakimi Achraf scored
                    else:
                        return "recommendation: p1"  # Hakimi Achraf did not score
                else:
                    return "recommendation: p4"  # Game not completed
    return "recommendation: p4"  # No data available or game not found

# Run the main function
if __name__ == "__main__":
    result = resolve_market()
    print(result)