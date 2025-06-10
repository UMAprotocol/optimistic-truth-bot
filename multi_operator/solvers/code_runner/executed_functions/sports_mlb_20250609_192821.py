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
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

# Function to make API requests
def make_request(endpoint, path, use_proxy=False):
    url = f"{PROXY_ENDPOINT if use_proxy else PRIMARY_ENDPOINT}{path}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if use_proxy:
            print("Proxy failed, trying primary endpoint")
            return make_request(endpoint, path, use_proxy=False)
        else:
            print(f"Failed to retrieve data: {e}")
            return None

# Function to determine the outcome of the NBA series
def resolve_nba_series():
    current_date = datetime.now()
    if current_date > datetime(2025, 7, 20, 23, 59):
        return "recommendation: p3"  # Market resolves 50-50 if postponed beyond July 20, 2025

    # Fetch playoff data
    playoff_data = make_request(PRIMARY_ENDPOINT, "/scores/json/PlayoffSeries")
    if playoff_data is None:
        return "recommendation: p4"  # Unable to fetch data

    # Check each series to find the Pacers vs. Knicks matchup
    for series in playoff_data:
        if series['Round'] == 3 and {'Indiana Pacers', 'New York Knicks'} == {series['HomeTeam'], series['AwayTeam']}:
            if series['Status'] == "Completed":
                if series['Winner'] == "Indiana Pacers":
                    return "recommendation: p2"  # Pacers advance
                elif series['Winner'] == "New York Knicks":
                    return "recommendation: p1"  # Knicks advance
            break

    return "recommendation: p4"  # Series not completed or not found

# Main execution
if __name__ == "__main__":
    result = resolve_nba_series()
    print(result)