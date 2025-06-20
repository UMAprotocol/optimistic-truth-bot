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

# Resolution conditions
RESOLUTION_MAP = {
    "No": "p1",
    "Yes": "p2",
    "50-50": "p3"
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

# Function to check if Evan Bouchard scored a goal
def check_goals(player_stats):
    for stat in player_stats:
        if stat['PlayerID'] == 8000:  # Assuming 8000 is Evan Bouchard's PlayerID
            goals = stat.get('Goals', 0)
            return "Yes" if goals > 0 else "No"
    return "No"

# Main function to resolve the market
def resolve_market():
    # Construct the URL for the specific game
    game_date = "2025-06-14"
    url = f"{PROXY_ENDPOINT}/scores/json/PlayerGameStatsByDate/{game_date}"

    # Make the request to the proxy endpoint
    data = make_request(url, HEADERS)
    if not data:
        # Fallback to primary endpoint if proxy fails
        url = f"{PRIMARY_ENDPOINT}/scores/json/PlayerGameStatsByDate/{game_date}"
        data = make_request(url, HEADERS)
        if not data:
            return "recommendation: " + RESOLUTION_MAP["50-50"]

    # Check if Evan Bouchard scored a goal
    result = check_goals(data)
    return "recommendation: " + RESOLUTION_MAP[result]

# Run the main function
if __name__ == "__main__":
    print(resolve_market())