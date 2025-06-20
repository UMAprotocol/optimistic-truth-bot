import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Constants
HLTV_EVENT_URL = "https://www.hltv.org/events/7902/blasttv-austin-major-2025"
MATCH_DATE = datetime(2025, 6, 10, 13, 30)  # 1:30 PM ET, converted to UTC
DELAY_THRESHOLD_DATE = datetime(2025, 6, 28, 23, 59)  # Latest acceptable delay date

# Load API keys
SPORTS_DATA_IO_CBB_API_KEY = os.getenv("SPORTS_DATA_IO_CBB_API_KEY")

# Headers for requests
HEADERS = {"Ocp-Apim-Subscription-Key": SPORTS_DATA_IO_CBB_API_KEY}

# Function to fetch match data from HLTV
def fetch_match_data():
    try:
        response = requests.get(HLTV_EVENT_URL, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

# Function to determine the outcome based on match data
def determine_outcome(match_data):
    if not match_data:
        return "p3"  # Assume 50-50 if data cannot be fetched

    # Extract relevant match information
    for match in match_data.get('matches', []):
        if match['team1']['name'] == "B8" and match['team2']['name'] == "Lynn Vision":
            match_time = datetime.strptime(match['date'], "%Y-%m-%dT%H:%M:%SZ")
            if match_time > DELAY_THRESHOLD_DATE:
                return "p3"  # Delayed beyond threshold
            if match['status'] == "Finished":
                if match['result']['team1'] > match['result']['team2']:
                    return "p2"  # B8 wins
                elif match['result']['team1'] < match['result']['team2']:
                    return "p1"  # Lynn Vision wins
            return "p3"  # Tie or other unresolved outcome

    return "p3"  # Default to 50-50 if no specific match info found

# Main execution function
def main():
    match_data = fetch_match_data()
    outcome = determine_outcome(match_data)
    print(f"recommendation: {outcome}")

if __name__ == "__main__":
    main()