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

# Function to check if Nemiga qualified for Stage 2
def check_nemiga_qualification():
    # Assuming the event ID and the team name are known and correct
    event_id = "7902"  # Example event ID for BLAST.tv Austin Major 2025
    team_name = "Nemiga"

    # Fetch the teams participating in the event
    teams_data = make_request(f"/scores/json/Teams/{event_id}", use_proxy=True)
    if teams_data:
        # Check if Nemiga is in the list of qualified teams
        if any(team['Name'] == team_name for team in teams_data):
            return "p2"  # Nemiga qualified
        else:
            return "p1"  # Nemiga did not qualify
    else:
        return "p3"  # Unable to determine

# Main execution
if __name__ == "__main__":
    result = check_nemiga_qualification()
    print(f"recommendation: {result}")