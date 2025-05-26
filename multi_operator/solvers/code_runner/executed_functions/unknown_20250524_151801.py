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
    """
    Function to fetch data from API with fallback to proxy.
    """
    try:
        # Try proxy endpoint first
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            # Fallback to primary endpoint if proxy fails
            response = requests.get(url.replace(PROXY_ENDPOINT, PRIMARY_ENDPOINT), headers=HEADERS, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

def check_trump_speech_for_term(date_of_event, term):
    """
    Check if the term is mentioned in Trump's speech on the given date.
    """
    # Construct the URL for the specific event
    url = f"{PROXY_ENDPOINT}/speeches/{date_of_event}/trump"
    data = get_data_from_api(url)
    
    if data and 'speech' in data:
        # Check if the term is in the speech
        return 'p2' if term.lower() in data['speech'].lower() else 'p1'
    else:
        # If data is not available or speech key is missing, assume event did not occur
        return 'p1'

if __name__ == "__main__":
    # Date of the event and term to search for
    date_of_event = "2025-05-24"
    term_to_search = "Beast"
    
    # Check if the term is mentioned in the speech
    recommendation = check_trump_speech_for_term(date_of_event, term_to_search)
    print(f"recommendation: {recommendation}")