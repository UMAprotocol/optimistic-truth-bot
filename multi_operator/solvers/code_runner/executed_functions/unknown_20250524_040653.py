import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API key loading
API_KEY = os.getenv("SPORTS_DATA_IO_NFL_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NFL_API_KEY")

# API endpoints
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/nfl"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/nfl-proxy"

# Headers for API requests
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

# Date range for the query
START_DATE = datetime(2025, 5, 17, 12, 0)  # May 17, 2025, 12:00 PM ET
END_DATE = datetime(2025, 5, 23, 23, 59)   # May 23, 2025, 11:59 PM ET

# Phrase to search for
SEARCH_PHRASE = "Peace through strength"

def get_statements(start_date, end_date):
    """
    Fetches public statements from Donald Trump within the specified date range.
    """
    url = f"{PROXY_ENDPOINT}/statements?start_date={start_date}&end_date={end_date}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            # Fallback to primary endpoint if proxy fails
            url = f"{PRIMARY_ENDPOINT}/statements?start_date={start_date}&end_date={end_date}"
            response = requests.get(url, headers=HEADERS, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                return None
    except requests.RequestException:
        return None

def check_phrase_in_statements(statements, phrase):
    """
    Checks if the specified phrase is mentioned in any of the statements.
    """
    for statement in statements:
        if phrase.lower() in statement['text'].lower():
            return True
    return False

def main():
    statements = get_statements(START_DATE.strftime('%Y-%m-%d'), END_DATE.strftime('%Y-%m-%d'))
    if statements is None:
        print("recommendation: p3")  # Unknown outcome due to data retrieval failure
    else:
        found = check_phrase_in_statements(statements, SEARCH_PHRASE)
        if found:
            print("recommendation: p2")  # Yes, phrase was mentioned
        else:
            print("recommendation: p1")  # No, phrase was not mentioned

if __name__ == "__main__":
    main()