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
        if endpoint == PROXY_ENDPOINT:
            print(f"Falling back to primary endpoint due to error: {e}")
            return make_request(PRIMARY_ENDPOINT, path)
        else:
            print(f"Error accessing API: {e}")
            return None

# Function to check if Denzel Dumfries scored in the final
def check_dumfries_goal():
    date_of_final = "2025-05-31"
    games_on_date = make_request(PROXY_ENDPOINT, f"GamesByDate/{date_of_final}")
    if not games_on_date:
        return "p4"  # Unable to retrieve data

    # Find the game between PSG and Inter Milan
    for game in games_on_date:
        if {'Paris Saint-Germain', 'Inter Milan'} == {game['HomeTeam'], game['AwayTeam']}:
            if game['Status'] != 'Final':
                return "p4"  # Game not completed
            # Check player goals
            player_stats = make_request(PROXY_ENDPOINT, f"PlayerGameStatsByGame/{game['GameID']}")
            for player in player_stats:
                if player['Name'] == 'Denzel Dumfries' and player['Goals'] > 0.5:
                    return "p2"  # Denzel Dumfries scored
            return "p1"  # No goals by Denzel Dumfries

    return "p4"  # Game not found or not the correct teams

# Main execution
if __name__ == "__main__":
    result = check_dumfries_goal()
    print(f"recommendation: {result}")