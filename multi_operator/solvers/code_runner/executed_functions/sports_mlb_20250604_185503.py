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
        print(f"Error: {e}")
        return None

# Function to check if Denzel Dumfries scored in the match
def check_dumfries_goal(game_id):
    game_stats = make_request(PRIMARY_ENDPOINT, f"PlayerGameStatsByGame/{game_id}")
    if game_stats:
        for player_stat in game_stats:
            if player_stat['Name'] == "Denzel Dumfries" and player_stat['Goals'] > 0.5:
                return True
    return False

# Main function to resolve the market
def resolve_market():
    # Define the date of the Champions League final
    match_date = "2025-05-31"
    # Attempt to retrieve the game data
    games_on_date = make_request(PRIMARY_ENDPOINT, f"GamesByDate/{match_date}")
    if not games_on_date:
        print("No games found or error in fetching data.")
        return "recommendation: p4"

    # Find the specific game
    for game in games_on_date:
        if game['HomeTeam'] == "Paris Saint-Germain" and game['AwayTeam'] == "Inter Milan":
            if datetime.now() < datetime(2025, 12, 31, 23, 59):
                if check_dumfries_goal(game['GameId']):
                    return "recommendation: p2"  # Yes, Dumfries scored
                else:
                    return "recommendation: p1"  # No, Dumfries did not score
            else:
                return "recommendation: p3"  # Market resolves to 50-50
    return "recommendation: p4"  # Game not found or not yet played

# Run the main function
if __name__ == "__main__":
    result = resolve_market()
    print(result)