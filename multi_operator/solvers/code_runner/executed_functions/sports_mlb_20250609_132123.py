import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NBA_API_KEY")

# Constants
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nba"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/sportsdata-io-nba-proxy"

# Function to make API requests
def make_request(endpoint, path):
    url = f"{endpoint}{path}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if endpoint == PROXY_ENDPOINT:
            print("Proxy failed, trying primary endpoint")
            return make_request(PRIMARY_ENDPOINT, path)
        else:
            print(f"Error: {e}")
            return None

# Function to determine the advancing team
def get_advancing_team():
    current_year = datetime.now().year
    path = f"/scores/json/PlayoffSeries/{current_year}"
    data = make_request(PROXY_ENDPOINT, path)
    if data:
        for series in data:
            if series['Round'] == 3:  # Western Conference Finals
                if series['Winner'] == "Oklahoma City Thunder":
                    return "p2"  # Thunder
                elif series['Winner'] == "Minnesota Timberwolves":
                    return "p1"  # Timberwolves
    return "p3"  # If no data or unresolved

# Main execution
if __name__ == "__main__":
    result = get_advancing_team()
    print(f"recommendation: {result}")