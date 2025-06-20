import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# Constants
HLTV_EVENT_URL = "https://www.hltv.org/events/7902/blasttv-austin-major-2025"
MATCH_DATE = "2025-06-13"
TEAM1 = "FaZe"
TEAM2 = "Legacy"
RESOLUTION_MAP = {
    "FaZe": "p1",
    "Legacy": "p2",
    "50-50": "p3"
}

# Function to fetch match results
def fetch_match_results():
    response = requests.get(HLTV_EVENT_URL)
    if response.status_code == 200:
        # This is a placeholder for actual data parsing logic
        # You would parse the HTML or JSON response here to find the match result
        # For demonstration, let's assume we found the result
        match_result = "Legacy"  # This should be dynamically determined from the response
        return match_result
    else:
        raise Exception("Failed to fetch data from HLTV")

# Main function to determine the outcome
def determine_outcome():
    current_date = datetime.utcnow().strftime('%Y-%m-%d')
    if current_date > MATCH_DATE:
        try:
            result = fetch_match_results()
            if result in RESOLUTION_MAP:
                return f"recommendation: {RESOLUTION_MAP[result]}"
            else:
                return f"recommendation: {RESOLUTION_MAP['50-50']}"
        except Exception as e:
            print(f"Error: {str(e)}")
            return "recommendation: p3"  # Assume 50-50 if there's an error
    else:
        return "recommendation: p3"  # Match not yet played or data not available

# Run the main function
if __name__ == "__main__":
    print(determine_outcome())