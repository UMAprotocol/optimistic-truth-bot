import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
DUNE_API_KEY = os.getenv("DUNE_API_KEY")
if not DUNE_API_KEY:
    raise ValueError("Missing DUNE_API_KEY")

# Configuration for headers and endpoints
HEADERS = {"Authorization": f"Bearer {DUNE_API_KEY}"}
PRIMARY_ENDPOINT = "https://dune.com/api/v1/query/123456/run"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/dune-proxy"

# Function to fetch data from Dune Analytics
def fetch_data(endpoint):
    try:
        response = requests.get(endpoint, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to fetch data: {response.status_code} {response.reason}")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Request failed: {e}")

# Main function to process the data and determine the outcome
def process_data():
    try:
        # Try fetching data from the proxy endpoint first
        data = fetch_data(PROXY_ENDPOINT)
    except Exception as e:
        print(f"Proxy failed, trying primary endpoint: {e}")
        # Fallback to the primary endpoint if proxy fails
        data = fetch_data(PRIMARY_ENDPOINT)

    # Extract the relevant data
    date_str = "2025-05-23"
    target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    tokens_count = data.get('data', {}).get(str(target_date), 0)

    # Determine the recommendation based on the token count
    if tokens_count >= 271:
        return "recommendation: p2"  # Yes
    else:
        return "recommendation: p1"  # No

# Run the main function and print the result
if __name__ == "__main__":
    result = process_data()
    print(result)