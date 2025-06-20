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
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/cbb/scores/json"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/cbb-proxy"

# Function to make API requests
def make_request(url, headers):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error during request: {e}")
        return None

# Function to check the match result
def check_match_result():
    event_date = "2025-06-13"
    teams = ("Aurora", "G2")
    url = f"{PROXY_ENDPOINT}/events/7902/blasttv-austin-major-2025"

    # Try proxy endpoint first
    result = make_request(url, HEADERS)
    if result is None:
        # Fallback to primary endpoint if proxy fails
        url = f"{PRIMARY_ENDPOINT}/events/7902/blasttv-austin-major-2025"
        result = make_request(url, HEADERS)

    if result:
        for match in result:
            if (match['Date'][:10] == event_date and
                match['HomeTeamName'] in teams and
                match['AwayTeamName'] in teams):
                if match['Status'] == 'Final':
                    if match['HomeTeamScore'] > match['AwayTeamScore']:
                        return "p1" if match['HomeTeamName'] == "G2" else "p2"
                    elif match['HomeTeamScore'] < match['AwayTeamScore']:
                        return "p1" if match['AwayTeamName'] == "G2" else "p2"
                elif match['Status'] in ['Canceled', 'Postponed']:
                    return "p3"
        return "p3"  # Default to 50-50 if no conclusive result
    else:
        return "p3"  # Default to 50-50 if no data available

# Main execution
if __name__ == "__main__":
    recommendation = check_match_result()
    print(f"recommendation: {recommendation}")