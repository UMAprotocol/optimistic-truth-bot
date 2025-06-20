import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
HLTV_API_KEY = os.getenv("SPORTS_DATA_IO_CBB_API_KEY")
if not HLTV_API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_CBB_API_KEY")

# Configuration for headers and endpoints
HEADERS = {"Ocp-Apim-Subscription-Key": HLTV_API_KEY}
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/cbb/scores/json"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/cbb-proxy"

# Function to make API requests
def make_request(url, headers):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

# Function to check the match result
def check_match_result():
    event_date = "2025-06-12"
    formatted_date = datetime.strptime(event_date, "%Y-%m-%d").strftime("%Y%m%d")
    url = f"{PROXY_ENDPOINT}/GamesByDate/{formatted_date}"
    result = make_request(url, HEADERS)
    if not result:
        url = f"{PRIMARY_ENDPOINT}/GamesByDate/{formatted_date}"
        result = make_request(url, HEADERS)
    
    if result:
        for game in result:
            if game['AwayTeam'] == "G2" and game['HomeTeam'] == "paiN":
                if game['Status'] == "Final":
                    if game['AwayTeamRuns'] > game['HomeTeamRuns']:
                        return "recommendation: p2"  # G2 wins
                    elif game['AwayTeamRuns'] < game['HomeTeamRuns']:
                        return "recommendation: p1"  # paiN wins
                elif game['Status'] in ["Canceled", "Postponed"]:
                    return "recommendation: p3"  # 50-50
        return "recommendation: p3"  # No clear result, assume 50-50
    else:
        return "recommendation: p3"  # Fallback to 50-50 if no data

# Main execution
if __name__ == "__main__":
    result = check_match_result()
    print(result)