import os
import requests
import logging
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_CBB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_CBB_API_KEY")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# API endpoints
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/cbb"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/cbb-proxy"

# Headers for API requests
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

def get_data_from_api(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        return None

def check_for_term_in_speech(date, term):
    # Construct the URL to fetch the speech transcript
    url = f"{PROXY_ENDPOINT}/speeches/{date}"
    data = get_data_from_api(url)
    if data and 'transcript' in data:
        return term.lower() in data['transcript'].lower()
    return False

def main():
    event_date = "2025-05-24"
    search_term = "Afghanistan"
    current_date = datetime.utcnow().date()
    event_date_obj = datetime.strptime(event_date, "%Y-%m-%d").date()

    # Check if the current date is past the event date
    if current_date > event_date_obj:
        found = check_for_term_in_speech(event_date, search_term)
        if found:
            print("recommendation: p2")  # Term found, resolves to "Yes"
        else:
            print("recommendation: p1")  # Term not found, resolves to "No"
    else:
        print("recommendation: p4")  # Event has not occurred yet

if __name__ == "__main__":
    main()