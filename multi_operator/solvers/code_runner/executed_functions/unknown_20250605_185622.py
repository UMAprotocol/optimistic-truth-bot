import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Constants
HLTV_EVENT_URL = "https://www.hltv.org/events/7902/blasttv-austin-major-2025"
TOURNAMENT_END_DATE = datetime.strptime("2025-07-28 23:59", "%Y-%m-%d %H:%M")

# Load API key for HLTV proxy (example, adjust as needed)
HLTV_API_KEY = os.getenv("SPORTS_DATA_IO_CBB_API_KEY")
if not HLTV_API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_CBB_API_KEY")

# Headers for HTTP requests
HEADERS = {"Ocp-Apim-Subscription-Key": HLTV_API_KEY}

# Function to get tournament data
def get_tournament_data():
    try:
        response = requests.get(HLTV_EVENT_URL, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Failed to fetch data: {e}")
        return None

# Main function to determine if OG qualifies for Stage 2
def check_og_qualification():
    data = get_tournament_data()
    if not data:
        return "p3"  # Unknown/50-50 if data cannot be fetched

    current_time = datetime.now()
    if current_time > TOURNAMENT_END_DATE:
        return "p1"  # No, if current time is past the tournament end date

    # Check if the tournament was postponed or canceled
    if data.get("status") in ["postponed", "canceled"]:
        return "p1"  # No, if tournament is postponed or canceled

    # Check if OG has qualified for Stage 2
    qualified_teams = data.get("qualified_teams", [])
    if "OG" in qualified_teams:
        return "p2"  # Yes, if OG is in the list of qualified teams

    return "p1"  # No, if OG is not in the list

# Run the main function and print the recommendation
if __name__ == "__main__":
    recommendation = check_og_qualification()
    print(f"recommendation: {recommendation}")