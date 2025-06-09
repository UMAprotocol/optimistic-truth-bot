import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Constants
HLTV_EVENT_URL = "https://www.hltv.org/events/7902/blasttv-austin-major-2025"
POSTPONEMENT_DATE = datetime.strptime("2025-07-28 23:59", "%Y-%m-%d %H:%M")

# Load API keys
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# Headers for requests
HEADERS = {
    "Authorization": f"Bearer {BINANCE_API_KEY}"
}

# Function to check if OG qualified for Stage 2
def check_og_qualification():
    try:
        response = requests.get(HLTV_EVENT_URL, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            # Simulate checking the content for qualification status
            # This is a placeholder: actual implementation will depend on the page structure
            if "OG qualifies for Stage 2" in response.text:
                return "p2"  # Yes
            else:
                return "p1"  # No
        else:
            print(f"Failed to fetch data: {response.status_code}")
            return "p3"  # Unknown/50-50 due to data fetch failure
    except requests.RequestException as e:
        print(f"Error during requests to HLTV: {e}")
        return "p3"  # Unknown/50-50 due to exception

# Main execution function
def main():
    current_time = datetime.now()
    if current_time > POSTPONEMENT_DATE:
        print("recommendation: p1")  # No, due to postponement or cancellation
    else:
        result = check_og_qualification()
        print(f"recommendation: {result}")

if __name__ == "__main__":
    main()