import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_CBB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_CBB_API_KEY")

# Configuration for headers and endpoints
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/cbb"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/cbb-proxy"

# Function to make HTTP GET requests
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
def resolve_match(date_str, player1, player2):
    games = get_data(f"/scores/json/GamesByDate/{date_str}")
    if games is None:
        return "p3"  # Assume unknown/50-50 if data retrieval fails

    for game in games:
        participants = {game['HomeTeam'], game['AwayTeam']}
        if player1 in participants and player2 in participants:
            if game['Status'] == "Final":
                winner = game['Winner']
                if winner == player1:
                    return "p1"
                elif winner == player2:
                    return "p2"
            elif game['Status'] in ["Canceled", "Postponed"]:
                return "p3"
    return "p3"  # Default to unknown/50-50 if no match found or other statuses

# Main execution function
if __name__ == "__main__":
    match_date = "2025-06-04"
    player1 = "Madison Keys"
    player2 = "Coco Gauff"
    result = resolve_match(match_date, player1, player2)
    print(f"recommendation: {result}")