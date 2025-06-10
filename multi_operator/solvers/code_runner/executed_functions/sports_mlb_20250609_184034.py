import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# Configuration for headers and API endpoints
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/mlb/scores/json"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/mlb-proxy"

# Function to make API requests
def make_request(endpoint, path):
    try:
        response = requests.get(f"{endpoint}/{path}", headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error during request to {endpoint}/{path}: {e}")
        return None

# Function to check if Goncalo Ramos scored in the game
def check_goncalo_ramos_score(game_id):
    game_boxscore = make_request(PRIMARY_ENDPOINT, f"BoxScore/{game_id}")
    if game_boxscore:
        for player in game_boxscore.get('PlayerGames', []):
            if player.get('Name') == "Goncalo Ramos":
                goals = player.get('Goals', 0)
                if goals > 0.5:
                    return True
    return False

# Main function to resolve the market
def resolve_market():
    # Define the date of the Champions League final
    final_date = "2025-05-31"
    current_date = datetime.now().strftime("%Y-%m-%d")

    # Check if the current date is past the final date
    if current_date > final_date:
        # Attempt to find the game data
        games_today = make_request(PROXY_ENDPOINT, f"GamesByDate/{final_date}") or \
                      make_request(PRIMARY_ENDPOINT, f"GamesByDate/{final_date}")
        if games_today:
            for game in games_today:
                if game['AwayTeam'] == "Inter Milan" and game['HomeTeam'] == "Paris Saint-Germain":
                    if check_goncalo_ramos_score(game['GameID']):
                        return "recommendation: p2"  # Yes, Goncalo Ramos scored
                    else:
                        return "recommendation: p1"  # No, Goncalo Ramos did not score
        return "recommendation: p3"  # 50-50, game data not conclusive or not found
    else:
        return "recommendation: p4"  # Too early to resolve

# Run the main function and print the result
if __name__ == "__main__":
    result = resolve_market()
    print(result)