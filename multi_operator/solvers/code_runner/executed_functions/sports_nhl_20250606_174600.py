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

# Resolution conditions based on the ancillary data
RESOLUTION_MAP = {
    "NRG": "p2",  # Qualifies for Stage 2
    "no_qualification": "p1",  # Does not qualify
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
        if use_proxy:
            print("Proxy failed, trying primary endpoint.")
            return make_request(url, use_proxy=False)
        else:
            print(f"HTTP Error: {e}")
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
    return None

# Function to check if NRG qualifies for Stage 2
def check_nrg_qualification():
    # Assuming the API provides a list of teams that qualified for Stage 2
    data = make_request("/scores/json/QualifiedTeams")
    if data:
        qualified_teams = [team['Team'] for team in data if 'Stage' in team and team['Stage'] == 2]
        if "NRG" in qualified_teams:
            return RESOLUTION_MAP["NRG"]
        else:
            return RESOLUTION_MAP["no_qualification"]
    return RESOLUTION_MAP["unknown"]

# Main execution
if __name__ == "__main__":
    result = check_nrg_qualification()
    print(f"recommendation: {result}")