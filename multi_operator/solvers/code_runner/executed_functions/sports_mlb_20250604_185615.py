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
    try:
        response = requests.get(f"{endpoint}/{path}", headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

# Function to check if Denzel Dumfries scored in the specified match
def check_dumfries_goal():
    # Define the match date and teams
    match_date = "2025-05-31"
    teams = ["Paris Saint-Germain", "Inter Milan"]
    player_name = "Denzel Dumfries"

    # Fetch games by date
    games = make_request(PRIMARY_ENDPOINT, f"GamesByDate/{match_date}")
    if not games:
        return "p4"  # Unable to fetch data

    # Find the specific game
    for game in games:
        if game['HomeTeam'] in teams and game['AwayTeam'] in teams:
            game_id = game['GameID']
            break
    else:
        return "p4"  # Game not found

    # Fetch game box score
    box_score = make_request(PRIMARY_ENDPOINT, f"BoxScore/{game_id}")
    if not box_score:
        return "p4"  # Unable to fetch box score

    # Check if Denzel Dumfries scored
    for player in box_score['PlayerGames']:
        if player['Name'] == player_name and player['Goals'] > 0.5:
            return "p2"  # Denzel Dumfries scored
        elif player['Name'] == player_name:
            return "p1"  # Denzel Dumfries did not score

    return "p1"  # Denzel Dumfries did not play or did not score

# Main function to run the check
if __name__ == "__main__":
    result = check_dumfries_goal()
    print(f"recommendation: {result}")