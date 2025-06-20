import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# Configuration for headers and endpoints
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/mlb/scores/json/GamesByDate/"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

# Function to make API requests
def make_request(url, use_proxy=False):
    endpoint = PROXY_ENDPOINT if use_proxy else PRIMARY_ENDPOINT
    try:
        response = requests.get(endpoint + url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if use_proxy:
            print("Proxy failed, trying primary endpoint.")
            return make_request(url, use_proxy=False)
        else:
            print(f"Failed to retrieve data: {e}")
            return None

# Function to check the occurrence of the word "Subway" in the debate
def check_subway_occurrences(date):
    games = make_request(date)
    if games is None:
        return "p4"  # Unable to retrieve data

    for game in games:
        if "Subway" in game['Summary']:  # Example condition, adjust based on actual data structure
            return "p2"  # Yes, "Subway" was mentioned 5+ times
    return "p1"  # No, "Subway" was not mentioned 5+ times

# Main execution function
if __name__ == "__main__":
    # Define the date of the event
    event_date = "2025-06-12"
    current_date = datetime.now().strftime("%Y-%m-%d")

    # Check if the current date is before the event date
    if current_date > event_date:
        result = check_subway_occurrences(event_date)
    else:
        result = "p4"  # Event has not occurred yet

    print(f"recommendation: {result}")