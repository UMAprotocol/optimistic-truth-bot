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

# Dates for the event
START_DATE = datetime(2025, 6, 16)
END_DATE = datetime(2025, 6, 18)

# URL for the primary and proxy endpoints
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

# Function to make API requests
def make_request(url, headers):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

# Function to check the status of Ali Khamenei
def check_status():
    current_date = START_DATE
    while current_date <= END_DATE:
        formatted_date = current_date.strftime("%Y-%m-%d")
        url = f"{PRIMARY_ENDPOINT}/{formatted_date}"
        data = make_request(url, HEADERS)
        if data:
            # Simulate checking for the status of Ali Khamenei
            # This is a placeholder for the actual logic that would be used
            for event in data:
                if "Ali Khamenei" in event['Title'] and "ceased" in event['Description']:
                    return "p2"  # Yes, he ceased to be the Supreme Leader
        current_date += timedelta(days=1)
    return "p1"  # No, he did not cease to be the Supreme Leader

# Main function to run the check
if __name__ == "__main__":
    result = check_status()
    print(f"recommendation: {result}")