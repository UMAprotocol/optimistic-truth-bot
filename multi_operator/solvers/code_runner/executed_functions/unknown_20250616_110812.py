import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API keys loaded from environment variables
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# Headers for API requests
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

# Define the date range for the query
START_DATE = datetime(2025, 6, 16)
END_DATE = datetime(2025, 6, 18)

# Function to check the status of Ali Khamenei
def check_status():
    # URLs for primary and proxy endpoints
    primary_url = "https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/"
    proxy_url = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

    # Iterate over each day in the date range
    current_date = START_DATE
    while current_date <= END_DATE:
        formatted_date = current_date.strftime("%Y-%m-%d")
        try:
            # Try proxy endpoint first
            response = requests.get(proxy_url + formatted_date, headers=HEADERS, timeout=10)
            if not response.ok:
                # If proxy fails, fall back to primary endpoint
                response = requests.get(primary_url + formatted_date, headers=HEADERS, timeout=10)
            if response.ok:
                data = response.json()
                # Check if the status indicates a change in leadership
                for event in data:
                    if "Ali Khamenei" in event['Title'] and "ceased" in event['Description']:
                        return "p2"  # Yes, he ceased to be the leader
        except requests.RequestException as e:
            print(f"Error fetching data for {formatted_date}: {e}")
        current_date += timedelta(days=1)

    # If no change in leadership status is found
    return "p1"  # No, he did not cease to be the leader

# Main execution
if __name__ == "__main__":
    result = check_status()
    print("recommendation:", result)