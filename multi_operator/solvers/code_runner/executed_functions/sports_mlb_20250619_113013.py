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
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

# Function to make API requests
def make_request(url, headers):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

# Function to find the game and determine the outcome
def find_game_and_determine_outcome(date, player1, player2):
    formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = PRIMARY_ENDPOINT + formatted_date
    games = make_request(url, HEADERS)
    if games:
        for game in games:
            teams = {game['HomeTeam'], game['AwayTeam']}
            if player1 in teams and player2 in teams:
                if game['Status'] == 'Final':
                    if game['Winner'] == player1:
                        return "p1"
                    elif game['Winner'] == player2:
                        return "p2"
                elif game['Status'] in ['Canceled', 'Postponed']:
                    return "p3"
    return "p4"

# Main execution function
def main():
    # Define the date and players based on the specific event
    date = "2025-06-19"
    player1 = "Felix Auger-Aliassime"
    player2 = "Karen Khachanov"

    # Determine the outcome based on the game data
    outcome = find_game_and_determine_outcome(date, player1, player2)
    print(f"recommendation: {outcome}")

if __name__ == "__main__":
    main()