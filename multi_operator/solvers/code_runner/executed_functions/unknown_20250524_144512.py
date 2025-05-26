import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# ─────────── configuration ───────────
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_CBB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_CBB_API_KEY")
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

# ─────────── generic GET wrapper ───────────
def _get(url, tag, retries=3, backoff=1.5):
    for i in range(retries):
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            if response.ok:
                return response.json()
            if response.status_code == 429:
                time.sleep(backoff * (2 ** i))
        except requests.RequestException as e:
            if i == retries - 1:
                raise ConnectionError(f"Failed to retrieve data for {tag}: {e}")
    return None

# ─────────── main ───────────
def check_trump_speech():
    # Define the date of the event
    event_date = "2025-05-24"
    current_date = datetime.utcnow().strftime('%Y-%m-%d')
    
    # Check if the event is in the future
    if current_date < event_date:
        return "recommendation: p4"  # Event has not occurred yet

    # URL to fetch the video transcript or relevant data
    video_transcript_url = "https://api.sportsdata.io/v3/cbb/scores/json/News"  # Placeholder URL

    # Fetch the transcript data
    transcript_data = _get(video_transcript_url, "Trump Speech Transcript")
    
    # Check if the term "Dome" is mentioned in the transcript
    if transcript_data and any("Dome" in article['Content'] for article in transcript_data):
        return "recommendation: p2"  # Term "Dome" was mentioned
    else:
        return "recommendation: p1"  # Term "Dome" was not mentioned

# Run the function and print the result
if __name__ == "__main__":
    result = check_trump_speech()
    print(result)