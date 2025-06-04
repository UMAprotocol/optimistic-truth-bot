import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_CBB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_CBB_API_KEY")

# Configuration for headers and endpoints
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/cbb"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/cbb-proxy"

# Function to make API requests
def make_request(endpoint, path):
    try:
        response = requests.get(f"{endpoint}{path}", headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error during request to {endpoint}{path}: {e}")
        return None

# Function to resolve the market based on the match result
def resolve_market(match_data):
    if not match_data:
        return "p3"  # Unknown or 50-50 if no data available
    if match_data['Status'] == 'Final':
        if match_data['Winner'] == 'Madison Keys':
            return "p2"  # Keys wins
        elif match_data['Winner'] == 'Coco Gauff':
            return "p1"  # Gauff wins
    elif match_data['Status'] in ['Canceled', 'Postponed']:
        return "p3"  # 50-50 if canceled or postponed
    return "p3"  # Default to 50-50 for other cases

# Main function to execute the market resolution logic
def main():
    match_date = "2025-06-04"
    formatted_date = datetime.strptime(match_date, "%Y-%m-%d").strftime("%Y-%m-%d")
    match_path = f"/scores/json/GamesByDate/{formatted_date}"

    # Try proxy endpoint first
    match_data = make_request(PROXY_ENDPOINT, match_path)
    if not match_data:
        # Fallback to primary endpoint if proxy fails
        match_data = make_request(PRIMARY_ENDPOINT, match_path)

    # Resolve the market based on the match data
    recommendation = resolve_market(match_data)
    print(f"recommendation: {recommendation}")

if __name__ == "__main__":
    main()