import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_CBB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_CBB_API_KEY")

# Configuration for headers and endpoints
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/cbb/scores/json"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/cbb-proxy"

# Function to make a GET request to the API
def make_request(endpoint, path):
    url = f"{endpoint}/{path}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        if response.status_code in [502, 503, 504]:  # Proxy specific errors
            print(f"Proxy failed, trying primary endpoint. Error: {e}")
            response = requests.get(f"{PRIMARY_ENDPOINT}/{path}", headers=HEADERS, timeout=10)
            response.raise_for_status()
            return response.json()
        else:
            raise
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None

# Function to check if the term "Afghanistan" is mentioned in the speech
def check_speech_for_term(date):
    # Simulated function to fetch speech transcript (API endpoint hypothetical)
    speech_transcript = make_request(PROXY_ENDPOINT, f"Speeches/GetTranscript?date={date}")
    if speech_transcript and "Afghanistan" in speech_transcript['text']:
        return "p2"  # Yes
    else:
        return "p1"  # No

# Main execution function
if __name__ == "__main__":
    event_date = "2025-05-24"
    current_date = datetime.now().strftime("%Y-%m-%d")
    if current_date > event_date:
        recommendation = check_speech_for_term(event_date)
    else:
        recommendation = "p4"  # Event has not occurred yet

    print(f"recommendation: {recommendation}")