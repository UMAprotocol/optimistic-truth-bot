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
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/nhl-proxy"

# Resolution conditions mapping
RESOLUTION_MAP = {
    "No": "p1",
    "Yes": "p2",
    "50-50": "p3"
}

# Function to make requests to the API
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

# Function to check if Gonçalo Ramos scored in the match
def check_goal_scored(player_id, match_id):
    match_data = make_request(f"/scores/json/Game/{match_id}")
    if match_data:
        players_stats = match_data.get('PlayerStats', [])
        for player_stat in players_stats:
            if player_stat['PlayerID'] == player_id:
                goals = player_stat.get('Goals', 0)
                if goals > 0.5:
                    return "Yes"
    return "No"

# Main function to resolve the market
def resolve_market():
    # Date and teams for the UEFA Nations League Final
    match_date = "2025-06-08"
    teams = ["Portugal", "Spain"]
    player_name = "Gonçalo Ramos"

    # Find the match ID and player ID
    matches = make_request(f"/scores/json/GamesByDate/{match_date}")
    if not matches:
        return "50-50"

    match_id = None
    for match in matches:
        if match['HomeTeam'] in teams and match['AwayTeam'] in teams:
            match_id = match['GameID']
            break

    if not match_id:
        return "50-50"

    players = make_request(f"/scores/json/Players")
    player_id = None
    for player in players:
        if player['Name'] == player_name:
            player_id = player['PlayerID']
            break

    if not player_id:
        return "50-50"

    # Check if the player scored
    result = check_goal_scored(player_id, match_id)
    return RESOLUTION_MAP[result]

# Run the main function and print the recommendation
if __name__ == "__main__":
    recommendation = resolve_market()
    print(f"recommendation: {recommendation}")