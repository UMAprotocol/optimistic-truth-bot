import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
SPORTS_DATA_IO_CBB_API_KEY = os.getenv("SPORTS_DATA_IO_CBB_API_KEY")

# API configuration
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/cbb"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/cbb-proxy"

# Headers for API requests
HEADERS = {"Ocp-Apim-Subscription-Key": SPORTS_DATA_IO_CBB_API_KEY}

def get_data_from_proxy(url):
    """ Attempt to fetch data using the proxy endpoint. """
    try:
        response = requests.get(f"{PROXY_ENDPOINT}{url}", headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Proxy failed with error: {e}")
        return None

def get_data_from_primary(url):
    """ Fallback to the primary endpoint if proxy fails. """
    try:
        response = requests.get(f"{PRIMARY_ENDPOINT}{url}", headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Primary endpoint failed with error: {e}")
        return None

def fetch_event_data():
    """ Fetch data related to the event and check for the specific term usage. """
    event_date = "2025-05-24"
    term = "Dome"
    url = f"/scores/json/GamesByDate/{event_date}"

    # Try fetching data via proxy first
    data = get_data_from_proxy(url)
    if data is None:
        # Fallback to primary endpoint if proxy fails
        data = get_data_from_primary(url)

    if data:
        for event in data:
            if "West Point Commencement" in event.get("Name", ""):
                # Check if the term is mentioned in the event description
                if term.lower() in event.get("Description", "").lower():
                    return "p2"  # Term found, resolve to Yes
        return "p1"  # Term not found, resolve to No
    else:
        return "p3"  # Data fetch failed, resolve to unknown/50-50

if __name__ == "__main__":
    result = fetch_event_data()
    print(f"recommendation: {result}")