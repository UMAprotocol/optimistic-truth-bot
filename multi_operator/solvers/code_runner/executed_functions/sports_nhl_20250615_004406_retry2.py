import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
NHL_API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
if not NHL_API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NHL_API_KEY")

# Constants
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nhl"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/nhl-proxy"
HEADERS = {"Ocp-Apim-Subscription-Key": NHL_API_KEY}
GAME_DATE = "2025-06-14"
PLAYER_NAME = "Brad Marchand"
RESOLUTION_MAP = {
    "Yes": "p2",
    "No": "p1",
    "50-50": "p3"
}

# Function to fetch data from API
def fetch_data(url, headers):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

# Function to check player's performance
def check_player_performance(game_data, player_name):
    for player in game_data.get('PlayerStats', []):
        if player.get('Name') == player_name and player.get('Goals', 0) > 0.5:
            return "Yes"
    return "No"

# Main function to resolve the market
def resolve_market():
    # Construct URL for the game day
    url = f"{PROXY_ENDPOINT}/scores/json/GamesByDate/{GAME_DATE}"
    game_data = fetch_data(url, HEADERS)
    
    # Fallback to primary endpoint if proxy fails
    if game_data is None:
        url = f"{PRIMARY_ENDPOINT}/scores/json/GamesByDate/{GAME_DATE}"
        game_data = fetch_data(url, HEADERS)
        if game_data is None:
            return "recommendation: p4"  # Unable to fetch data

    # Check if the game has been played and if the player scored
    current_date = datetime.utcnow().date()
    game_date = datetime.strptime(GAME_DATE, "%Y-%m-%d").date()
    if current_date > game_date:
        for game in game_data:
            if game['Status'] == 'Final':
                result = check_player_performance(game, PLAYER_NAME)
                return f"recommendation: {RESOLUTION_MAP[result]}"
            elif game['Status'] in ['Postponed', 'Canceled']:
                return "recommendation: p3"
    elif current_date < game_date:
        return "recommendation: p4"  # Game has not been played yet

    return "recommendation: p4"  # Default case if no other condition is met

# Execute the function and print the result
if __name__ == "__main__":
    result = resolve_market()
    print(result)