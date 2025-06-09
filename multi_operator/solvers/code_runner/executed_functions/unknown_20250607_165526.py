import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API keys loaded from environment variables
HLTV_API_KEY = os.getenv("SPORTS_DATA_IO_CBB_API_KEY")

# Constants for the event
EVENT_DATE = "2025-06-07"
TEAM_1 = "3DMAX"
TEAM_2 = "BetBoom"
EVENT_URL = "https://www.hltv.org/events/7902/blasttv-austin-major-2025"

# Headers for API requests
HEADERS = {"Ocp-Apim-Subscription-Key": HLTV_API_KEY}

def fetch_match_result():
    """
    Fetches the match result from the HLTV event page.
    """
    try:
        response = requests.get(EVENT_URL, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            # Simulated parsing logic, as actual HTML parsing is not shown
            # This is a placeholder to represent how you might check for the winner
            # In practice, you would parse the HTML or JSON response to find the match result
            if "3DMAX wins" in response.text:
                return "p2"  # 3DMAX wins
            elif "BetBoom wins" in response.text:
                return "p1"  # BetBoom wins
            elif "match is postponed" in response.text or "match is canceled" in response.text:
                return "p3"  # Match postponed or canceled
        elif response.status_code == 404:
            print("Event page not found.")
        else:
            response.raise_for_status()
    except requests.RequestException as e:
        print(f"An error occurred: {e}")
    return "p3"  # Default to unknown/50-50 if unable to fetch or parse

if __name__ == "__main__":
    # Ensure the current date is not before the event date
    current_date = datetime.now().strftime("%Y-%m-%d")
    if current_date < EVENT_DATE:
        print("recommendation: p4")  # Event has not occurred yet
    else:
        result = fetch_match_result()
        print(f"recommendation: {result}")