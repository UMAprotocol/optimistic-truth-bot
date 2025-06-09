import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NHL_API_KEY")

# Constants
EVENT_URL = "https://www.hltv.org/events/7902/blasttv-austin-major-2025"
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
MATCH_DATE = datetime(2025, 6, 5, 11, 0)  # June 5, 2025, 11:00 AM ET
DELAY_THRESHOLD = datetime(2025, 6, 28)  # June 28, 2025

# Resolution map based on the ancillary data provided
RESOLUTION_MAP = {
    "Complexity": "p2",  # Complexity win
    "TYLOO": "p1",       # TYLOO win
    "50-50": "p3",       # Tie, cancel, or delay
    "Too early to resolve": "p4"
}

def fetch_match_result():
    try:
        response = requests.get(EVENT_URL, timeout=10)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching data from HLTV: {e}")
        return None

def parse_match_result(html_content):
    if not html_content:
        return "Too early to resolve"
    
    # Simplified example of parsing, real implementation would need actual HTML parsing logic
    if "Complexity win" in html_content:
        return "Complexity"
    elif "TYLOO win" in html_content:
        return "TYLOO"
    elif "match delayed" in html_content or "match canceled" in html_content:
        return "50-50"
    else:
        return "Too early to resolve"

def resolve_market():
    current_time = datetime.now()
    if current_time < MATCH_DATE:
        return RESOLUTION_MAP["Too early to resolve"]
    elif current_time > DELAY_THRESHOLD:
        return RESOLUTION_MAP["50-50"]
    
    match_html = fetch_match_result()
    match_result = parse_match_result(match_html)
    return RESOLUTION_MAP.get(match_result, "Too early to resolve")

if __name__ == "__main__":
    recommendation = resolve_market()
    print(f"recommendation: {recommendation}")