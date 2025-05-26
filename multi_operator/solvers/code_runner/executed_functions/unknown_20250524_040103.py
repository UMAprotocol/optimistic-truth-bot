import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API keys loaded from environment variables
API_KEY = os.getenv("SPORTS_DATA_IO_NFL_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NFL_API_KEY")

# Configuration for headers and endpoints
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nfl/scores/json"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/nfl-proxy"

# Function to make API requests
def make_request(endpoint, path):
    url = f"{endpoint}/{path}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error during request to {url}: {str(e)}")
        return None

# Function to check if Trump said "Genius" in any NFL video
def check_trump_mentions(start_date, end_date):
    # Format dates for API
    start_date_str = start_date.strftime("%Y-%m-%d")
    end_date_str = end_date.strftime("%Y-%m-%d")

    # Attempt to use proxy endpoint first
    data = make_request(PROXY_ENDPOINT, f"GamesByDate/{start_date_str}/{end_date_str}")
    if data is None:
        # Fallback to primary endpoint if proxy fails
        data = make_request(PRIMARY_ENDPOINT, f"GamesByDate/{start_date_str}/{end_date_str}")

    if data:
        for game in data:
            # Example of checking video descriptions or titles for the word "Genius"
            description = game.get("Description", "").lower()
            if "genius" in description:
                return True
    return False

# Main function to run the check
def main():
    # Define the time period from the question
    start_date = datetime(2025, 5, 17, 12, 0)
    end_date = datetime(2025, 5, 23, 23, 59)

    # Check for mentions of "Genius"
    mentioned = check_trump_mentions(start_date, end_date)

    # Print recommendation based on whether "Genius" was mentioned
    if mentioned:
        print("recommendation: p2")  # Yes
    else:
        print("recommendation: p1")  # No

if __name__ == "__main__":
    main()