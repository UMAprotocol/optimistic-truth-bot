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

# Function to check if Calhanoglu Hakan scored in the match
def check_calhanoglu_goal():
    # Define the date of the match
    match_date = "2025-05-31"
    # Define the teams involved
    teams = ["Paris Saint-Germain", "Inter Milan"]
    # Define the player of interest
    player_name = "Calhanoglu Hakan"

    # Fetch games by date
    games = make_request(PROXY_ENDPOINT, f"GamesByDate/{match_date}")
    if not games:
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

    # Fetch player game stats
    player_stats = make_request(PROXY_ENDPOINT, f"PlayerGameStatsByGame/{game_id}")
    if not player_stats:
        player_stats = make_request(PRIMARY_ENDPOINT, f"PlayerGameStatsByGame/{game_id}")
    if not player_stats:
        return "p4"  # Unable to fetch player stats

    # Check if Calhanoglu Hakan scored
    for stat in player_stats:
        if stat['Name'] == player_name and stat['Goals'] > 0:
            return "p2"  # Yes, he scored
    return "p1"  # No, he did not score

# Main execution
if __name__ == "__main__":
    result = check_calhanoglu_goal()
    print(f"recommendation: {result}")