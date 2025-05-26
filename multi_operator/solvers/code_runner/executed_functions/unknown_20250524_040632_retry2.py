import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# Configuration for headers
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

# Function to make GET requests
def make_request(url, retries=3, backoff=1.5):
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                time.sleep(backoff * (2 ** attempt))
        except requests.RequestException as e:
            print(f"Request failed: {e}")
    return None

# Function to check if Trump mentioned "Peace through strength"
def check_trump_statement(start_date, end_date):
    # Example URL, needs to be replaced with actual endpoint for Trump's statements
    url = f"https://api.example.com/statements?start_date={start_date}&end_date={end_date}"
    data = make_request(url)
    if data:
        for statement in data:
            if "Peace through strength" in statement['text']:
                return "p2"  # Yes, mentioned
    return "p1"  # No, not mentioned

# Main execution
if __name__ == "__main__":
    start_date = datetime(2025, 5, 17, 12, 0)  # Start date and time
    end_date = datetime(2025, 5, 23, 23, 59)  # End date and time
    recommendation = check_trump_statement(start_date.isoformat(), end_date.isoformat())
    print(f"recommendation: {recommendation}")