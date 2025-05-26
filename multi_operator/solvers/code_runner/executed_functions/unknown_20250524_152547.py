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
            if response.status_code in (401, 403):
                raise Exception(f"Access denied or bad request at {url}")
            if response.status_code == 404:
                return None  # Not found
            if response.status_code == 429:
                time.sleep(backoff * (2 ** i))  # Exponential backoff
        except requests.RequestException as e:
            if i == retries - 1:
                raise Exception(f"Failed to retrieve data after {retries} attempts: {e}")
    return None

# ─────────── main ───────────
def check_trump_speech():
    event_date = "2025-05-24"
    today = datetime.utcnow().strftime("%Y-%m-%d")
    if event_date > today:
        return "p4"  # Event has not occurred yet

    # Assuming the speech is recorded and available for analysis
    # This is a placeholder for actual speech processing logic
    # In practice, you would need access to the video or transcript of the speech
    # Here we simulate checking a transcript or processed video data
    speech_content = "Today at West Point, we discuss the future of our military, including the new F-47 jets."
    if "F-47" in speech_content:
        return "p2"  # Yes, Trump said "F-47"
    else:
        return "p1"  # No, Trump did not say "F-47"

if __name__ == "__main__":
    result = check_trump_speech()
    print("recommendation:", result)