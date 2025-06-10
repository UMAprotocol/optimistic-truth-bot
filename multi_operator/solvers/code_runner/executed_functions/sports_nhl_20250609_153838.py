import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
NHL_API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
if not NHL_API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NHL_API_KEY")

# Configuration for API access
HEADERS = {"Ocp-Apim-Subscription-Key": NHL_API_KEY}
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

# Function to check if Connor McDavid scored in the game
def check_mcdavid_score(game_id):
    game_boxscore = make_request(f"/scores/json/BoxScore/{game_id}")
    if game_boxscore:
        for player in game_boxscore['PlayerGames']:
            if player['Name'] == "Connor McDavid":
                if player['Goals'] >= 1:
                    return "p2"  # Yes, scored 1+ goals
    return "p1"  # No goals

# Main function to resolve the market
def resolve_market():
    date_of_game = "2025-05-29"
    games_on_date = make_request(f"/scores/json/GamesByDate/{date_of_game}")
    if games_on_date:
        for game in games_on_date:
            if game['AwayTeam'] == "EDM" and game['HomeTeam'] == "DAL" or \
               game['HomeTeam'] == "EDM" and game['AwayTeam'] == "DAL":
                if game['Status'] == "Final":
                    return check_mcdavid_score(game['GameID'])
                elif game['Status'] in ["Canceled", "Postponed"]:
                    return "p1"  # Game not played as scheduled
    return "p1"  # Default to no if no data found or game not completed as expected

# Execute the function and print the recommendation
if __name__ == "__main__":
    recommendation = resolve_market()
    print(f"recommendation: {recommendation}")