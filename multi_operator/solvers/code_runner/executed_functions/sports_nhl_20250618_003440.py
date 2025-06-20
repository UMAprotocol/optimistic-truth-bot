import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NHL_API_KEY")

# Configuration for headers and endpoints
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nhl"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-nhl-proxy"

# Resolution map based on the ancillary data provided
RESOLUTION_MAP = {
    "Yes": "p2",  # Player scored more than 0.5 goals
    "No": "p1",   # Player did not score more than 0.5 goals
    "50-50": "p3" # Game not completed by the specified date
}

# Function to make API requests
def make_request(url, headers):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

# Function to check if Sam Reinhart scored in the game
def check_player_score(game_id, player_name):
    url = f"{PRIMARY_ENDPOINT}/scores/json/PlayerGameStatsByGame/{game_id}"
    game_stats = make_request(url, HEADERS)
    if game_stats:
        for stat in game_stats:
            if stat['Name'] == player_name and stat['Goals'] > 0.5:
                return "Yes"
    return "No"

# Main function to resolve the market
def resolve_market():
    # Define the game and player details
    game_date = "2025-06-17"
    player_name = "Sam Reinhart"
    team1 = "EDM"
    team2 = "FLA"

    # Construct the URL to fetch games on the specified date
    url = f"{PRIMARY_ENDPOINT}/scores/json/GamesByDate/{game_date}"
    games = make_request(url, HEADERS)
    if games:
        for game in games:
            if {game['HomeTeam'], game['AwayTeam']} == {team1, team2}:
                if datetime.now() < datetime(2025, 12, 31, 23, 59):
                    score_result = check_player_score(game['GameID'], player_name)
                    return f"recommendation: {RESOLUTION_MAP[score_result]}"
                else:
                    return f"recommendation: {RESOLUTION_MAP['50-50']}"
    return "recommendation: p4"  # If no games found or other issues

# Run the main function
if __name__ == "__main__":
    result = resolve_market()
    print(result)