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
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/nhl-proxy"

# Resolution map based on the outcome
RESOLUTION_MAP = {
    "YES": "p2",  # Player scored more than 0.5 goals
    "NO": "p1",   # Player did not score more than 0.5 goals
    "UNKNOWN": "p3"  # Game not completed or data unavailable
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

# Function to check player's goal in a specific game
def check_player_goal(game_id, player_name):
    url = f"{PRIMARY_ENDPOINT}/scores/json/PlayerGameStatsByGame/{game_id}"
    data = fetch_data(url, HEADERS)
    if data:
        for player in data:
            if player["Name"] == player_name and player["Goals"] > 0.5:
                return "YES"
        return "NO"
    return "UNKNOWN"

# Main function to determine the outcome
def main():
    game_date = "2025-06-17"
    player_name = "Aleksander Barkov"
    team1 = "EDM"
    team2 = "FLA"

    # Construct the URL to fetch games on a specific date
    games_url = f"{PRIMARY_ENDPOINT}/scores/json/GamesByDate/{game_date}"
    games_data = fetch_data(games_url, HEADERS)

    if games_data:
        for game in games_data:
            if team1 in game["HomeTeam"] and team2 in game["AwayTeam"]:
                result = check_player_goal(game["GameID"], player_name)
                print(f"recommendation: {RESOLUTION_MAP[result]}")
                return
    print("recommendation: p3")  # If no game data found or API fails

if __name__ == "__main__":
    main()