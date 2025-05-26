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

def get_data_from_api(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
    except requests.exceptions.ConnectionError as conn_err:
        print(f"Connection error occurred: {conn_err}")
    except requests.exceptions.Timeout as timeout_err:
        print(f"Timeout error occurred: {timeout_err}")
    except requests.exceptions.RequestException as req_err:
        print(f"Error occurred: {req_err}")
    return None

def check_trump_speech_for_term(date_of_event, term):
    # Construct the URL for the event's speech data
    url = f"{PROXY_ENDPOINT}/speeches/{date_of_event}"
    data = get_data_from_api(url)
    if data and 'speech' in data:
        if term.lower() in data['speech'].lower():
            return "p2"  # Term found, resolve to Yes
        else:
            return "p1"  # Term not found, resolve to No
    return "p1"  # Default to No if data is not available or no speech found

if __name__ == "__main__":
    # Date of the event and term to search for
    event_date = "2025-05-24"
    search_term = "Afghanistan"

    # Check if the term is mentioned in the speech
    recommendation = check_trump_speech_for_term(event_date, search_term)
    print(f"recommendation: {recommendation}")