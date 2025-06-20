import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
HLTV_API_KEY = os.getenv("SPORTS_DATA_IO_CBB_API_KEY")
if not HLTV_API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_CBB_API_KEY")

# Configuration for headers and API endpoints
HEADERS = {"Ocp-Apim-Subscription-Key": HLTV_API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/cbb"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/cbb-proxy"

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
    # Match details
    event_date = "2025-06-12"
    team1 = "Liquid"
    team2 = "Lynn Vision"
    match_date = datetime.strptime(event_date, "%Y-%m-%d")

    # Check if today's date is before the match date
    if datetime.now() < match_date:
        return "recommendation: p4"  # Match has not occurred yet

    # API request to fetch match results
    results = make_request(f"/scores/json/GamesByDate/{event_date}", use_proxy=True)
    if results is None:
        return "recommendation: p3"  # Unable to fetch results, assume unknown

    # Find the specific match
    for match in results:
        if team1 in match['HomeTeamName'] and team2 in match['AwayTeamName']:
            if match['Status'] == "Final":
                if match['HomeTeamScore'] > match['AwayTeamScore']:
                    return "recommendation: p2"  # Liquid wins
                elif match['HomeTeamScore'] < match['AwayTeamScore']:
                    return "recommendation: p1"  # Lynn Vision wins
                else:
                    return "recommendation: p3"  # Tie
            elif match['Status'] in ["Canceled", "Postponed"]:
                return "recommendation: p3"  # Canceled or postponed
            else:
                return "recommendation: p4"  # In progress or other non-final status

    # If no match found or other conditions
    return "recommendation: p3"  # Assume unknown or 50-50 if no match data

# Main execution
if __name__ == "__main__":
    result = resolve_match()
    print(result)