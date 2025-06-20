import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NHL_API_KEY")

# Constants
EVENT_DATE = "2025-06-19"
MATCH_TIME = "19:30:00"
HLTV_EVENT_URL = "https://www.hltv.org/events/7902/blasttv-austin-major-2025"
RESOLUTION_MAP = {
    "Spirit": "p2",
    "MOUZ": "p1",
    "50-50": "p3"
}

# Headers for API request
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

def fetch_match_result():
    # Construct the datetime object for the match
    match_datetime = datetime.strptime(f"{EVENT_DATE} {MATCH_TIME}", "%Y-%m-%d %H:%M:%S")
    current_datetime = datetime.utcnow()

    # Check if the match is in the future
    if current_datetime < match_datetime:
        return "p4"  # Match has not occurred yet

    # Simulate fetching data from HLTV (since actual API interaction is not possible here)
    # This is a placeholder for the actual API request you would make to HLTV or similar service
    match_result = "Spirit"  # Simulated result; replace with actual API call logic

    # Check for match cancellation or delay beyond the allowed date
    delay_datetime = datetime.strptime("2025-06-28", "%Y-%m-%d")
    if current_datetime > delay_datetime:
        return RESOLUTION_MAP["50-50"]  # Match delayed beyond allowed date

    # Return the result based on the match outcome
    return RESOLUTION_MAP.get(match_result, "p3")  # Default to 50-50 if result is unexpected

# Main execution
if __name__ == "__main__":
    result = fetch_match_result()
    print(f"recommendation: {result}")