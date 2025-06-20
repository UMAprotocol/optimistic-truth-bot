import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API keys loaded from environment variables
API_KEY = os.getenv("SPORTS_DATA_IO_CBB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_CBB_API_KEY")

# Headers for API requests
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

# URL configurations
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/cbb"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/cbb-proxy"

# Function to make GET requests to the API
def get_data(url, use_proxy=False):
    endpoint = PROXY_ENDPOINT if use_proxy else PRIMARY_ENDPOINT
    full_url = f"{endpoint}{url}"
    try:
        response = requests.get(full_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if use_proxy:
            print("Proxy failed, trying primary endpoint.")
            return get_data(url, use_proxy=False)
        else:
            print(f"Failed to retrieve data: {e}")
            return None

# Function to determine the outcome of the match
def resolve_match():
    # Date and players hardcoded based on the specific event
    match_date = "2025-06-11"
    player1 = "Arthur Rinderknech"
    player2 = "Marton Fucsovics"

    # Format the API request URL
    url = f"/scores/json/GamesByDate/{match_date}"

    # Get data from the API
    data = get_data(url, use_proxy=True)
    if data:
        for game in data:
            if player1 in game['Players'] and player2 in game['Players']:
                if game['Status'] == "Final":
                    winner = game['Winner']
                    if winner == player1:
                        return "recommendation: p2"  # Rinderknech wins
                    elif winner == player2:
                        return "recommendation: p1"  # Fucsovics wins
                elif game['Status'] in ["Canceled", "Postponed"]:
                    return "recommendation: p3"  # Match canceled or postponed
    return "recommendation: p3"  # Default to unknown/50-50 if no conclusive data

# Main execution
if __name__ == "__main__":
    result = resolve_match()
    print(result)