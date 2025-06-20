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
        print(f"Error during request to {url}: {str(e)}")
        return None

# Function to resolve the match outcome
def resolve_match(date_str, player1, player2):
    # Format the date and prepare the API path
    date_formatted = datetime.strptime(date_str, "%Y-%m-%d").strftime("%Y-%m-%d")
    path = f"GamesByDate/{date_formatted}"

    # Try proxy endpoint first
    games = make_request(PROXY_ENDPOINT, path)
    if games is None:
        # Fallback to primary endpoint if proxy fails
        games = make_request(PRIMARY_ENDPOINT, path)
        if games is None:
            return "p4"  # Unable to resolve due to API failure

    # Search for the specific match
    for game in games:
        if (player1 in game['HomeTeam'] or player1 in game['AwayTeam']) and \
           (player2 in game['HomeTeam'] or player2 in game['AwayTeam']):
            if game['Status'] == 'Final':
                if game['Winner'] == player1:
                    return "p1"
                elif game['Winner'] == player2:
                    return "p2"
            elif game['Status'] in ['Canceled', 'Postponed']:
                return "p3"
            else:
                return "p4"  # Match not completed yet

    return "p4"  # Match not found or not yet started

# Main execution function
if __name__ == "__main__":
    # Match details
    match_date = "2025-06-19"
    player1 = "Alexander Bublik"
    player2 = "Jannik Sinner"

    # Resolve the match and print the recommendation
    recommendation = resolve_match(match_date, player1, player2)
    print(f"recommendation: {recommendation}")