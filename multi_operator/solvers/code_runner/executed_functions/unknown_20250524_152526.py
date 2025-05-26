import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API keys loaded from environment variables
SPORTS_DATA_IO_CBB_API_KEY = os.getenv("SPORTS_DATA_IO_CBB_API_KEY")

# API endpoints
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/cbb"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/cbb-proxy"

# Headers for API requests
HEADERS = {"Ocp-Apim-Subscription-Key": SPORTS_DATA_IO_CBB_API_KEY}

def get_data_from_proxy(url):
    """ Attempt to fetch data using the proxy endpoint """
    try:
        response = requests.get(f"{PROXY_ENDPOINT}{url}", headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Proxy failed with error: {e}")
        return None

def get_data_from_primary(url):
    """ Fallback to the primary endpoint if proxy fails """
    try:
        response = requests.get(f"{PRIMARY_ENDPOINT}{url}", headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Primary endpoint failed with error: {e}")
        return None

def fetch_event_data(event_date):
    """ Fetch event data for the specified date """
    formatted_date = event_date.strftime("%Y-%m-%d")
    url = f"/scores/json/GamesByDate/{formatted_date}"
    data = get_data_from_proxy(url)
    if data is None:
        data = get_data_from_primary(url)
    return data

def check_for_phrase(data, phrase):
    """ Check if the phrase is mentioned in the event data """
    for event in data:
        if phrase in event.get('Summary', ''):
            return True
    return False

def main():
    event_date = datetime(2025, 5, 24)
    phrase_to_check = "F-47"
    data = fetch_event_data(event_date)
    if data and check_for_phrase(data, phrase_to_check):
        print("recommendation: p2")  # Yes, phrase was mentioned
    else:
        print("recommendation: p1")  # No, phrase was not mentioned

if __name__ == "__main__":
    main()