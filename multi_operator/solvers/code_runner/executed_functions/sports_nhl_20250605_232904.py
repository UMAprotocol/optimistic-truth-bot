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

# Resolution map based on the ancillary data provided
RESOLUTION_MAP = {
    "Nemiga": "p2",  # Yes, Nemiga qualifies
    "no_qualify": "p1",  # No, Nemiga does not qualify
    "unknown": "p3"  # Unknown or 50-50
}

# Function to make API requests
def make_request(url, headers):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

# Function to check qualification status
def check_qualification():
    # Construct URL to fetch event details
    event_url = f"{PROXY_ENDPOINT}/scores/json/Events/7902"
    event_details = make_request(event_url, HEADERS)
    if not event_details:
        # Fallback to primary endpoint if proxy fails
        event_url = f"{PRIMARY_ENDPOINT}/scores/json/Events/7902"
        event_details = make_request(event_url, HEADERS)
    
    if event_details:
        # Check if Nemiga is listed as qualified
        for team in event_details.get('Teams', []):
            if team.get('Name') == "Nemiga" and team.get('Qualified'):
                return RESOLUTION_MAP["Nemiga"]
        return RESOLUTION_MAP["no_qualify"]
    else:
        return RESOLUTION_MAP["unknown"]

# Main execution
if __name__ == "__main__":
    result = check_qualification()
    print(f"recommendation: {result}")