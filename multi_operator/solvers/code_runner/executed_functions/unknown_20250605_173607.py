import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Constants
EVENT_DATE = "2025-06-05"
MATCH_TIME = "11:00 AM ET"
TEAM1 = "Imperial"
TEAM2 = "Legacy"
EVENT_URL = "https://www.hltv.org/events/7902/blasttv-austin-major-2025"

# Load API key from environment
HLTV_API_KEY = os.getenv("SPORTS_DATA_IO_CBB_API_KEY")
if not HLTV_API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_CBB_API_KEY")

# Headers for HTTP requests
HEADERS = {"Ocp-Apim-Subscription-Key": HLTV_API_KEY}

def get_match_result():
    # Convert event date and time to datetime object
    event_datetime = datetime.strptime(f"{EVENT_DATE} {MATCH_TIME}", "%Y-%m-%d %I:%M %p ET")
    current_datetime = datetime.now()

    # Check if the match is scheduled for a future date
    if current_datetime < event_datetime:
        return "p4"  # Match has not occurred yet

    # Make a request to the HLTV API to fetch match results
    try:
        response = requests.get(EVENT_URL, headers=HEADERS)
        if response.status_code == 200:
            match_data = response.json()
            # Assuming the API returns a list of matches and we find the correct one
            for match in match_data:
                if match['team1']['name'] == TEAM1 and match['team2']['name'] == TEAM2:
                    if match['status'] == 'Finished':
                        if match['winner'] == TEAM1:
                            return "p2"  # Imperial wins
                        elif match['winner'] == TEAM2:
                            return "p1"  # Legacy wins
                    elif match['status'] in ['Canceled', 'Postponed']:
                        return "p3"  # Match canceled or postponed
        else:
            print(f"Failed to fetch data: {response.status_code}")
            return "p3"  # Assume unknown/50-50 if data fetch fails
    except Exception as e:
        print(f"Error fetching match data: {str(e)}")
        return "p3"  # Assume unknown/50-50 on error

    # If no data found or match is still scheduled
    return "p4"

# Main execution
if __name__ == "__main__":
    result = get_match_result()
    print(f"recommendation: {result}")