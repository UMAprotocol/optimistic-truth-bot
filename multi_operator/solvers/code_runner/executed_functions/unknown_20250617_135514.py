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
    # Date and players specific to the query
    match_date = "2025-06-17"
    player1 = "Joao Fonseca"
    player2 = "Flavio Cobolli"

    # Format the date for the API request
    formatted_date = datetime.strptime(match_date, "%Y-%m-%d").strftime("%Y-%m-%d")

    # Get the schedule for the specified date
    schedule = get_data(f"/scores/json/GamesByDate/{formatted_date}", use_proxy=True)

    if schedule is None:
        return "recommendation: p3"  # Unknown or API failure

    # Search for the specific match
    for game in schedule:
        if player1 in game['HomeTeam'] or player1 in game['AwayTeam']:
            if player2 in game['HomeTeam'] or player2 in game['AwayTeam']:
                if game['Status'] == "Final":
                    winner = game['Winner']
                    if winner == player1:
                        return "recommendation: p2"  # Fonseca wins
                    elif winner == player2:
                        return "recommendation: p1"  # Cobolli wins
                elif game['Status'] in ["Canceled", "Postponed"]:
                    return "recommendation: p3"  # Match canceled or postponed
                else:
                    return "recommendation: p3"  # Match not completed or other status

    # If no match found or no conclusive result
    return "recommendation: p3"

# Main execution
if __name__ == "__main__":
    result = resolve_match()
    print(result)