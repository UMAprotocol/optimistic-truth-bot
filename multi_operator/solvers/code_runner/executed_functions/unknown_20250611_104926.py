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
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/cbb/scores/json"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/cbb-proxy"

# Function to make API requests
def make_request(endpoint, path):
    try:
        response = requests.get(f"{endpoint}/{path}", headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error during request to {endpoint}/{path}: {e}")
        return None

# Function to resolve the market based on the match result
def resolve_market(match_date, player1, player2):
    # Format the date for the API request
    formatted_date = datetime.strptime(match_date, "%Y-%m-%d").strftime("%Y-%m-%d")
    games_today = make_request(PROXY_ENDPOINT, f"GamesByDate/{formatted_date}")

    if not games_today:
        games_today = make_request(PRIMARY_ENDPOINT, f"GamesByDate/{formatted_date}")
        if not games_today:
            return "recommendation: p3"  # Return 50-50 if data is unavailable

    # Search for the specific match
    for game in games_today:
        if player1 in game['Players'] and player2 in game['Players']:
            if game['Status'] == "Final":
                winner = game['Winner']
                if winner == player1:
                    return "recommendation: p2"  # Rinderknech wins
                elif winner == player2:
                    return "recommendation: p1"  # Fucsovics wins
            elif game['Status'] in ["Canceled", "Postponed"]:
                return "recommendation: p3"  # Match canceled or postponed

    # If no specific match found or match is still scheduled
    return "recommendation: p3"  # Return 50-50 if match is not completed or found

# Main execution function
if __name__ == "__main__":
    match_date = "2025-06-11"
    player1 = "Arthur Rinderknech"
    player2 = "Marton Fucsovics"
    result = resolve_market(match_date, player1, player2)
    print(result)