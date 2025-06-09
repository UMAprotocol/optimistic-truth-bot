import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NHL_API_KEY")

# Configuration for API access
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nhl"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/nhl-proxy"

# Resolution map based on the outcome
RESOLUTION_MAP = {
    "p1": "No",  # Gonçalo Ramos did not score
    "p2": "Yes",  # Gonçalo Ramos scored
    "p3": "50-50"  # Match not completed or other indeterminate outcome
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

# Main function to determine the outcome
def resolve_market():
    # Construct the URL for the specific game and player
    game_date = "2025-06-08"
    player_name = "Gonçalo Ramos"
    team_name = "Portugal"
    opponent_team_name = "Spain"

    # Try fetching from the proxy endpoint first
    url = f"{PROXY_ENDPOINT}/scores/json/GamesByDate/{game_date}"
    data = fetch_data(url, HEADERS)
    if not data:
        # Fallback to the primary endpoint if proxy fails
        url = f"{PRIMARY_ENDPOINT}/scores/json/GamesByDate/{game_date}"
        data = fetch_data(url, HEADERS)

    if not data:
        return "recommendation: p4"  # Unable to fetch data

    # Analyze the fetched data
    for game in data:
        if game['HomeTeam'] == team_name or game['AwayTeam'] == team_name:
            if game['Status'] != "Final":
                return "recommendation: p4"  # Game not completed
            # Check player's performance
            for player in game['Players']:
                if player['Name'] == player_name:
                    goals = player['Goals']
                    if goals > 0.5:
                        return "recommendation: p2"  # Player scored
                    else:
                        return "recommendation: p1"  # Player did not score

    # If no relevant game or player data found
    return "recommendation: p4"

# Execute the main function and print the result
if __name__ == "__main__":
    result = resolve_market()
    print(result)