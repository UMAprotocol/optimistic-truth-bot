import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Constants
HLTV_EVENT_URL = "https://www.hltv.org/events/7902/blasttv-austin-major-2025"
MATCH_DATE = datetime(2025, 6, 12, 11, 0)  # June 12, 2025, 11:00 AM ET
END_DATE = datetime(2025, 6, 28)  # June 28, 2025

# Load API keys
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
SPORTS_DATA_IO_MLB_API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
SPORTS_DATA_IO_NBA_API_KEY = os.getenv("SPORTS_DATA_IO_NBA_API_KEY")
SPORTS_DATA_IO_NFL_API_KEY = os.getenv("SPORTS_DATA_IO_NFL_API_KEY")
SPORTS_DATA_IO_NHL_API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
SPORTS_DATA_IO_CFB_API_KEY = os.getenv("SPORTS_DATA_IO_CFB_API_KEY")
SPORTS_DATA_IO_CBB_API_KEY = os.getenv("SPORTS_DATA_IO_CBB_API_KEY")

# Function to fetch match result from HLTV
def fetch_match_result():
    try:
        response = requests.get(HLTV_EVENT_URL, timeout=10)
        response.raise_for_status()
        # Simulated parsing logic (actual parsing would depend on the page structure)
        if "Vitality win" in response.text:
            return "p2"  # Vitality wins
        elif "Legacy win" in response.text:
            return "p1"  # Legacy wins
        elif "match is tied" in response.text or "match postponed" in response.text:
            return "p3"  # Tie or postponed
    except requests.RequestException as e:
        print(f"Error fetching data from HLTV: {e}")
        return "p3"  # Default to 50-50 in case of error

# Main function to determine the outcome
def resolve_market():
    current_time = datetime.now()
    if current_time < MATCH_DATE:
        return "p4"  # Too early / in-progress
    elif current_time > END_DATE:
        return "p3"  # Resolve as 50-50 if delayed beyond end date
    else:
        result = fetch_match_result()
        return result

# Run the resolver and print the recommendation
if __name__ == "__main__":
    recommendation = resolve_market()
    print(f"recommendation: {recommendation}")