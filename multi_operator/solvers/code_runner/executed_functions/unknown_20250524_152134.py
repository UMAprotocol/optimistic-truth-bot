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

def get_data_from_api(url, proxy=False):
    """ Fetch data from API with fallback to proxy if needed """
    endpoint = PROXY_ENDPOINT if proxy else PRIMARY_ENDPOINT
    full_url = f"{endpoint}{url}"
    try:
        response = requests.get(full_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if not proxy:
            print("Primary endpoint failed, trying proxy...")
            return get_data_from_api(url, proxy=True)
        else:
            print(f"Both primary and proxy endpoints failed: {e}")
            return None

def check_trump_speech_for_term(date, term):
    """ Check if the term is mentioned in Trump's speech on the given date """
    # Simulated API endpoint for fetching speech transcripts
    speech_data = get_data_from_api(f"/speeches/{date}/trump")
    if speech_data and 'transcript' in speech_data:
        return term.lower() in speech_data['transcript'].lower()
    return False

def main():
    # Date of the event
    event_date = "2025-05-24"
    # Term to check in the speech
    term_to_check = "river"

    # Check if the term is mentioned in the speech
    if check_trump_speech_for_term(event_date, term_to_check):
        print("recommendation: p2")  # Term mentioned
    else:
        print("recommendation: p1")  # Term not mentioned

if __name__ == "__main__":
    main()