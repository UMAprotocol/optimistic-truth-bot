import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
HLTV_URL = "https://www.hltv.org/events/7902/blasttv-austin-major-2025"

# Constants for resolution
TEAM_COMPLEXITY = "Complexity"
TEAM_TYLOO = "TYLOO"
MATCH_DATE = datetime(2025, 6, 5, 11, 0)  # June 5, 2025, 11:00 AM ET
DELAY_THRESHOLD = datetime(2025, 6, 28)  # June 28, 2025

# Resolution map based on the ancillary data provided
RESOLUTION_MAP = {
    TEAM_TYLOO: "p1",
    TEAM_COMPLEXITY: "p2",
    "50-50": "p3",
    "Too early to resolve": "p4",
}

def fetch_match_data(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching data from HLTV: {e}")
        return None

def parse_match_result(html_content):
    if not html_content:
        return "p4"  # Unable to fetch data, consider as unresolved

    # Simplified example of parsing - in practice, use BeautifulSoup or similar
    if TEAM_COMPLEXITY in html_content and TEAM_TYLOO in html_content:
        if "match postponed" in html_content or "match canceled" in html_content:
            return RESOLUTION_MAP["50-50"]
        elif TEAM_COMPLEXITY + " wins" in html_content:
            return RESOLUTION_MAP[TEAM_COMPLEXITY]
        elif TEAM_TYLOO + " wins" in html_content:
            return RESOLUTION_MAP[TEAM_TYLOO]
        else:
            return RESOLUTION_MAP["50-50"]  # Assume tie or unresolved status
    return "p4"  # Match not found or data insufficient

def resolve_market():
    current_time = datetime.now()
    if current_time < MATCH_DATE:
        return RESOLUTION_MAP["Too early to resolve"]
    elif current_time > DELAY_THRESHOLD:
        return RESOLUTION_MAP["50-50"]

    html_content = fetch_match_data(HLTV_URL)
    return parse_match_result(html_content)

if __name__ == "__main__":
    recommendation = resolve_market()
    print(f"recommendation: {recommendation}")