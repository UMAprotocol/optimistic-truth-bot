import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# Constants
EVENT_DATE = "2025-06-12"
EVENT_TIME = "18:15"
TEAM1 = "FaZe"
TEAM2 = "MOUZ"
HLTV_URL = "https://www.hltv.org/events/7902/blasttv-austin-major-2025"

# Headers for HTTP requests
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

def get_match_result():
    try:
        # Convert event date and time to datetime object
        event_datetime = datetime.strptime(f"{EVENT_DATE} {EVENT_TIME}", "%Y-%m-%d %H:%M")
        current_datetime = datetime.utcnow()

        # Check if the event is in the future
        if current_datetime < event_datetime:
            return "p4"  # Event has not occurred yet

        # Fetch data from HLTV
        response = requests.get(HLTV_URL, timeout=10)
        if response.status_code == 200:
            # Parse the response to find the match result
            # This is a placeholder for actual parsing logic
            match_data = response.json()
            for match in match_data.get('matches', []):
                if match['team1']['name'] == TEAM1 and match['team2']['name'] == TEAM2:
                    if match['result']['winner'] == TEAM1:
                        return "p1"
                    elif match['result']['winner'] == TEAM2:
                        return "p2"
            # If no result is found, assume the match was postponed or canceled
            return "p3"
        else:
            # Handle non-200 responses
            return "p3"
    except requests.RequestException as e:
        # Handle request exceptions
        print(f"Error fetching match data: {str(e)}")
        return "p3"

# Main execution
if __name__ == "__main__":
    result = get_match_result()
    print(f"recommendation: {result}")