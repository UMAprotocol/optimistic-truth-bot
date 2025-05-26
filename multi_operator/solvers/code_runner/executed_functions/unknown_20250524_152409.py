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
                time.sleep(backoff * 2**i)
        except requests.RequestException as e:
            print(f"Error during {tag} request: {str(e)}")
    return None

# ─────────── main ───────────
def check_trump_speech():
    event_date = "2025-05-24"
    today = datetime.utcnow().strftime("%Y-%m-%d")
    if event_date > today:
        return "p4"  # Event is in the future

    # Assuming the video or transcript is available at a specific URL
    # This is a placeholder for the actual implementation
    video_url = "https://example.com/trump_west_point_speech_2025.mp4"
    try:
        response = requests.get(video_url)
        if response.ok and "Space Force" in response.text:
            return "p2"  # Yes, Trump said "Space Force"
        else:
            return "p1"  # No, Trump did not say "Space Force"
    except requests.RequestException:
        return "p3"  # Unknown/50-50 due to error in fetching or processing the video

if __name__ == "__main__":
    result = check_trump_speech()
    print("recommendation:", result)