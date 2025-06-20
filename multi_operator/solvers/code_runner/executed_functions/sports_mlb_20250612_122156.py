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
        print(f"Error: {e}")
        return None

# Function to find the game and determine the outcome
def find_game_and_determine_outcome(date, player1, player2):
    # Format the date for the API request
    formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m-%d")
    games_today = make_request(PRIMARY_ENDPOINT, f"GamesByDate/{formatted_date}")
    if not games_today:
        games_today = make_request(PROXY_ENDPOINT, f"GamesByDate/{formatted_date}")
        if not games_today:
            return "p4"  # Unable to retrieve data

    # Search for the specific game
    for game in games_today:
        if player1 in game['HomeTeam'] or player1 in game['AwayTeam']:
            if player2 in game['HomeTeam'] or player2 in game['AwayTeam']:
                # Check the game status
                if game['Status'] == 'Final':
                    if game['Winner'] == player1:
                        return "p2"  # Perricard wins
                    elif game['Winner'] == player2:
                        return "p1"  # Aliassime wins
                elif game['Status'] in ['Canceled', 'Postponed']:
                    return "p3"  # Game not played or postponed
                return "p4"  # Game not final yet
    return "p4"  # Game not found or no conclusive result

# Main function to run the script
if __name__ == "__main__":
    # Define the match details
    match_date = "2025-06-12"
    player1 = "Giovanni Mpetshi Perricard"
    player2 = "Felix Auger-Aliassime"

    # Get the outcome
    outcome = find_game_and_determine_outcome(match_date, player1, player2)
    print(f"recommendation: {outcome}")