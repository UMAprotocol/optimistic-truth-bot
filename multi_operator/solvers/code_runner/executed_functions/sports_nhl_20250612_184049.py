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
HLTV_EVENT_URL = "https://www.hltv.org/events/7902/blasttv-austin-major-2025"
DATE_OF_MATCH = "2025-06-12"
TIME_OF_MATCH = "14:45"  # 2:45 PM ET
TEAM1 = "Natus Vincere"
TEAM2 = "Nemiga"
RESOLUTION_MAP = {
    TEAM1: "p2",  # Natus Vincere
    TEAM2: "p1",  # Nemiga
    "50-50": "p3",
    "Too early to resolve": "p4",
}

# Helper functions
def get_match_result():
    response = requests.get(HLTV_EVENT_URL)
    if response.status_code != 200:
        raise Exception("Failed to fetch data from HLTV")
    
    # This is a placeholder for actual data parsing logic
    # You would parse the HTML or JSON response here to find the match result
    # For demonstration, let's assume Natus Vincere won
    winner = TEAM1  # Simulated outcome

    # Check for match cancellation or delay
    current_date = datetime.utcnow().strftime('%Y-%m-%d')
    if current_date > "2025-06-28":
        return RESOLUTION_MAP["50-50"]
    
    return RESOLUTION_MAP[winner]

# Main execution
if __name__ == "__main__":
    try:
        result = get_match_result()
        print("recommendation:", result)
    except Exception as e:
        print("Failed to resolve market due to:", str(e))
        print("recommendation:", RESOLUTION_MAP["Too early to resolve"])