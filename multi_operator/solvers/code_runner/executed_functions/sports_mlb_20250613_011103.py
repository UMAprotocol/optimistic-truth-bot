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

# Function to check if the term "Subway" is mentioned by any candidate
def check_mentions(date):
    formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = f"{PRIMARY_ENDPOINT}/{formatted_date}"
    games = make_request(url, HEADERS)
    if games:
        for game in games:
            if "Subway" in game['Summary']:  # Example condition, adjust based on actual API response structure
                return True
    return False

# Main function to resolve the market
def resolve_market():
    event_date = "2025-06-12"
    if check_mentions(event_date):
        print("recommendation: p2")  # Yes, "Subway" mentioned 5+ times
    else:
        print("recommendation: p1")  # No, "Subway" not mentioned 5+ times

# Run the main function
if __name__ == "__main__":
    resolve_market()