import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
SPORTS_DATA_IO_CBB_API_KEY = os.getenv("SPORTS_DATA_IO_CBB_API_KEY")

# Constants
HLTV_EVENT_URL = "https://www.hltv.org/events/7902/blasttv-austin-major-2025"
HEADERS = {"Ocp-Apim-Subscription-Key": SPORTS_DATA_IO_CBB_API_KEY}

# Function to fetch data from HLTV
def fetch_match_result():
    try:
        response = requests.get(HLTV_EVENT_URL, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

# Analyze the match result
def analyze_match(data):
    if not data:
        return "p3"  # Assume 50-50 if data fetching fails

    # Example data processing logic
    match_info = data.get('matches', {}).get('3DMAX vs Legacy', {})
    if match_info.get('status') == 'canceled':
        return "p3"  # 50-50 if canceled
    elif match_info.get('winner') == '3DMAX':
        return "p2"  # 3DMAX wins
    elif match_info.get('winner') == 'Legacy':
        return "p1"  # Legacy wins
    else:
        return "p3"  # 50-50 for any other case (e.g., tie or no result)

# Main function to run the program
def main():
    match_data = fetch_match_result()
    recommendation = analyze_match(match_data)
    print(f"recommendation: {recommendation}")

if __name__ == "__main__":
    main()