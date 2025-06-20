import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Constants
HLTV_EVENT_URL = "https://www.hltv.org/events/7902/blasttv-austin-major-2025"
MATCH_DATE = "2025-06-12"
MATCH_TIME = "15:35"
TEAM_AURORA = "Aurora"
TEAM_FURIA = "FURIA"

# Load API key for HLTV proxy (assuming it's set up similarly to Binance proxy in the environment)
HLTV_PROXY_API_KEY = os.getenv("BINANCE_API_KEY")
HLTV_PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

# Headers for HLTV proxy request
HEADERS = {
    "Authorization": f"Bearer {HLTV_PROXY_API_KEY}"
}

# Function to fetch match results
def fetch_match_result():
    try:
        response = requests.get(HLTV_EVENT_URL, headers=HEADERS, timeout=10)
        response.raise_for_status()
        matches = response.json().get('matches', [])
        
        # Find the match by date and teams
        for match in matches:
            if match['date'].startswith(MATCH_DATE) and match['time'] == MATCH_TIME:
                if TEAM_AURORA in match['teams'] and TEAM_FURIA in match['teams']:
                    if match['result'] == TEAM_AURORA:
                        return "p2"  # Aurora wins
                    elif match['result'] == TEAM_FURIA:
                        return "p1"  # FURIA wins
                    else:
                        return "p3"  # Tie or other unresolved outcome
        return "p3"  # No match found or no result available
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return "p3"  # Assume unresolved on error

# Main execution
if __name__ == "__main__":
    result = fetch_match_result()
    print(f"recommendation: {result}")