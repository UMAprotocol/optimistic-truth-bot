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

# Function to make API requests
def make_request(endpoint, path):
    url = f"{endpoint}/{path}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        return None

# Function to check for the term "Dome" in the speech
def check_for_term(speech_text, term):
    return term.lower() in speech_text.lower()

# Main function to process the event and determine the outcome
def process_event():
    # Define the date of the event and the term to search for
    event_date = "2025-05-24"
    term_to_search = "Dome"

    # Check if today's date is before the event date
    if datetime.now().date() < datetime.strptime(event_date, "%Y-%m-%d").date():
        return "recommendation: p4"  # Event has not occurred yet

    # Attempt to fetch the speech transcript from the proxy endpoint
    speech_data = make_request(PROXY_ENDPOINT, "SpeechTranscript")
    if not speech_data:
        # Fallback to the primary endpoint if proxy fails
        speech_data = make_request(PRIMARY_ENDPOINT, "SpeechTranscript")

    # Check if the speech data was successfully retrieved
    if not speech_data:
        return "recommendation: p1"  # Assume "No" if data cannot be retrieved

    # Check if the term is mentioned in the speech
    if check_for_term(speech_data.get('transcript', ''), term_to_search):
        return "recommendation: p2"  # Term is mentioned
    else:
        return "recommendation: p1"  # Term is not mentioned

# Run the main function and print the result
if __name__ == "__main__":
    result = process_event()
    print(result)