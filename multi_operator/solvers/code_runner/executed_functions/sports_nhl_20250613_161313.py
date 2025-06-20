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
TEAM_LEGACY = "Legacy"
TEAM_FAZE = "FaZe"
DEADLINE_DATE = "2025-06-28"

# Resolution map based on the outcome
RESOLUTION_MAP = {
    TEAM_FAZE: "p1",
    TEAM_LEGACY: "p2",
    "50-50": "p3"
}

# Function to fetch match results
def fetch_match_result():
    try:
        response = requests.get(HLTV_EVENT_URL, timeout=10)
        response.raise_for_status()
        # Simulated parsing logic, replace with actual HTML parsing or API response handling
        # This is a placeholder to demonstrate where and how you would parse the response
        if "Legacy wins" in response.text:
            return TEAM_LEGACY
        elif "FaZe wins" in response.text:
            return TEAM_FAZE
        elif "match delayed" in response.text or "match canceled" in response.text:
            return "50-50"
    except requests.RequestException as e:
        print(f"Error fetching match results: {e}")
        return None

# Main function to determine the outcome
def resolve_market():
    today = datetime.utcnow().date()
    match_date = datetime.strptime(MATCH_DATE, "%Y-%m-%d").date()
    deadline_date = datetime.strptime(DEADLINE_DATE, "%Y-%m-%d").date()

    if today < match_date:
        return "recommendation: p4"  # Too early to resolve
    elif today > deadline_date:
        return "recommendation: p3"  # Resolve as 50-50 if beyond deadline

    result = fetch_match_result()
    if result:
        return f"recommendation: {RESOLUTION_MAP[result]}"
    else:
        return "recommendation: p3"  # Default to 50-50 if no conclusive result

# Execute the main function
if __name__ == "__main__":
    print(resolve_market())