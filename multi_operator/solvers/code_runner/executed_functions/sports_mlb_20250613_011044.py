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
def make_request(url, headers):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error during request: {e}")
        return None

# Function to check the occurrence of the word "Subway" in the debate
def check_subway_occurrences(date):
    formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = PRIMARY_ENDPOINT + formatted_date
    games = make_request(url, HEADERS)
    if games is None:
        print("Failed to retrieve data from primary endpoint, trying proxy...")
        games = make_request(PROXY_ENDPOINT, HEADERS)
        if games is None:
            return "p4"  # Unable to resolve due to data retrieval issues

    subway_count = sum(game['Summary'].lower().count('subway') for game in games if 'Summary' in game)
    return "p2" if subway_count >= 5 else "p1"

# Main execution
if __name__ == "__main__":
    event_date = "2025-06-12"
    result = check_subway_occurrences(event_date)
    print(f"recommendation: {result}")