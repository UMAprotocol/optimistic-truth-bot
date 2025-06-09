import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API key for HLTV (placeholder, as HLTV does not provide a public API key)
HLTV_API_KEY = os.getenv("HLTV_API_KEY")

# Configuration for HTTP requests
HEADERS = {"Ocp-Apim-Subscription-Key": HLTV_API_KEY}

# URL for the BLAST.tv Austin Major 2025 event
EVENT_URL = "https://www.hltv.org/events/7902/blasttv-austin-major-2025"

# Function to fetch data from HLTV
def fetch_event_data(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

# Function to determine the outcome of the match
def determine_outcome(data):
    if not data:
        return "p3"  # Assume 50-50 if data fetching fails or is incomplete

    # Example logic to parse the data and find the match result
    # This is a placeholder since actual data structure is unknown
    for match in data.get('matches', []):
        if match['team1'] == "TYLOO" and match['team2'] == "Lynn Vision":
            if match['result'] == "win":
                return "p2" if match['winner'] == "TYLOO" else "p1"
            elif match['result'] in ["tie", "canceled", "postponed"]:
                return "p3"

    return "p3"  # Default to 50-50 if no specific match info is found

# Main execution function
def main():
    event_data = fetch_event_data(EVENT_URL)
    recommendation = determine_outcome(event_data)
    print(f"recommendation: {recommendation}")

if __name__ == "__main__":
    main()