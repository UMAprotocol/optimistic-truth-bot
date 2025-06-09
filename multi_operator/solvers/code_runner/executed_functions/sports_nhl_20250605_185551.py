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
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/nhl-proxy"

# Resolution conditions based on the team abbreviations
RESOLUTION_MAP = {
    "OG": "p2",  # Team OG qualifies
    "not_qualified": "p1",  # Team OG does not qualify
    "unknown": "p3"  # Unknown or 50-50
}

# Function to make requests to the API
def make_request(url, use_proxy=False):
    endpoint = PROXY_ENDPOINT if use_proxy else PRIMARY_ENDPOINT
    full_url = f"{endpoint}{url}"
    try:
        response = requests.get(full_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        if response.status_code in [502, 503, 504] and not use_proxy:
            # Retry with proxy if primary fails with server errors
            return make_request(url, use_proxy=True)
        else:
            raise e
    except requests.exceptions.RequestException as e:
        raise e

# Function to check if OG qualifies for Stage 2
def check_qualification():
    current_date = datetime.utcnow().strftime("%Y-%m-%d")
    if current_date > "2025-07-28":
        return "p1"  # Resolve to "no" if the date is past the threshold

    try:
        # Assuming the API provides a list of qualified teams
        data = make_request("/scores/json/QualifiedTeams")
        qualified_teams = [team['TeamId'] for team in data if team['Stage'] == 2]
        # Assuming 'OG' has a specific TeamId that we know, e.g., 1234
        if 1234 in qualified_teams:
            return RESOLUTION_MAP["OG"]
        else:
            return RESOLUTION_MAP["not_qualified"]
    except Exception as e:
        print(f"Error occurred: {e}")
        return RESOLUTION_MAP["unknown"]

# Main execution
if __name__ == "__main__":
    result = check_qualification()
    print(f"recommendation: {result}")