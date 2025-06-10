import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NBA_API_KEY")

# Configuration for headers and endpoints
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
    # Check if the current year matches the event year
    if current_year != 2025:
        return "p4"  # Too early to resolve

    # API path to get the playoff bracket
    path = f"/scores/json/PlayoffBracket/{current_year}"
    data = make_request(PROXY_ENDPOINT, path)

    if data is None:
        return "p3"  # Unable to retrieve data, resolve as unknown

    # Search for the Western Conference Finals result
    for item in data:
        if item['Round'] == 'Western Conference Finals':
            if datetime.strptime(item['Updated'], "%Y-%m-%dT%H:%M:%S") > datetime(2025, 7, 20, 23, 59):
                return "p3"  # Postponed beyond the limit
            if item['Winner'] == 'Oklahoma City Thunder':
                return "p2"  # Thunder advanced
            elif item['Winner'] == 'Minnesota Timberwolves':
                return "p1"  # Timberwolves advanced

    return "p3"  # No clear winner found or data issues

# Main execution
if __name__ == "__main__":
    result = get_advancing_team()
    print(f"recommendation: {result}")