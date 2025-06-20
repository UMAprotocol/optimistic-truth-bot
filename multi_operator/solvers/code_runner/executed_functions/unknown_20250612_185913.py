import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_CBB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_CBB_API_KEY")

# Configuration for headers and API endpoints
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/cbb"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-cbb-proxy"

# Function to make API requests
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

# Function to determine the outcome of the match
def resolve_match():
    # Specific match details
    event_date = "2025-06-12"
    team1 = "Liquid"
    team2 = "Lynn Vision"
    match_id = "551697"

    # Fetch match results
    results = make_request(f"/scores/json/GamesByDate/{event_date}", use_proxy=True)
    if results:
        for game in results:
            if game['GlobalGameID'] == match_id:
                if game['Status'] == "Final":
                    if game['AwayTeam'] == team1 and game['HomeTeamScore'] < game['AwayTeamScore']:
                        return "recommendation: p2"  # Liquid wins
                    elif game['HomeTeam'] == team1 and game['HomeTeamScore'] > game['AwayTeamScore']:
                        return "recommendation: p2"  # Liquid wins
                    elif game['AwayTeam'] == team2 and game['HomeTeamScore'] < game['AwayTeamScore']:
                        return "recommendation: p1"  # Lynn Vision wins
                    elif game['HomeTeam'] == team2 and game['HomeTeamScore'] > game['AwayTeamScore']:
                        return "recommendation: p1"  # Lynn Vision wins
                    else:
                        return "recommendation: p3"  # Tie or error in scoring
                elif game['Status'] in ["Canceled", "Postponed"]:
                    return "recommendation: p3"  # Canceled or postponed
                else:
                    return "recommendation: p3"  # In progress or other non-final status
    return "recommendation: p3"  # Default to unknown if no data found or match not found

# Main execution
if __name__ == "__main__":
    result = resolve_match()
    print(result)