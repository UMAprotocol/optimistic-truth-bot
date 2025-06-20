import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_CBB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_CBB_API_KEY")

# Configuration
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/cbb"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/cbb-proxy"

# Function to handle API requests
def get_api_data(url, use_proxy=False):
    endpoint = PROXY_ENDPOINT if use_proxy else PRIMARY_ENDPOINT
    full_url = f"{endpoint}{url}"
    try:
        response = requests.get(full_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if use_proxy:
            print("Proxy failed, trying primary endpoint.")
            return get_api_data(url, use_proxy=False)
        else:
            print(f"API request failed: {e}")
            return None

# Main function to determine the outcome
def resolve_match():
    # Match details
    match_date = "2025-06-17"
    player1 = "Jordan Thompson"
    player2 = "Jaume Munar"

    # Fetch match data
    match_data = get_api_data(f"/scores/json/GamesByDate/{match_date}", use_proxy=True)
    if match_data is None:
        return "recommendation: p3"  # Unable to fetch data, resolve as unknown/50-50

    # Find the specific match
    for match in match_data:
        if player1 in match['Players'] and player2 in match['Players']:
            if match['Status'] == "Final":
                winner = match['Winner']
                if winner == player1:
                    return "recommendation: p2"  # Thompson wins
                elif winner == player2:
                    return "recommendation: p1"  # Munar wins
            elif match['Status'] in ["Canceled", "Postponed"]:
                return "recommendation: p3"  # Match canceled or postponed

    # If no match found or match is not final
    return "recommendation: p4"  # Match not found or not completed

# Execute the function and print the result
if __name__ == "__main__":
    result = resolve_match()
    print(result)