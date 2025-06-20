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
def make_request(endpoint, path):
    url = f"{endpoint}/{path}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        if endpoint == PROXY_ENDPOINT:
            print("Proxy failed, trying primary endpoint")
            return make_request(PRIMARY_ENDPOINT, path)
        else:
            print(f"HTTP Error: {e}")
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
    return None

# Function to determine the outcome of the match
def determine_outcome(data):
    if not data:
        return "p3"  # Assume 50-50 if no data could be retrieved
    for event in data:
        if event['Name'] == "MOUZ vs. FaZe" and event['Day'] == "2025-06-12":
            if event['Status'] == "Final":
                if event['Winner'] == "MOUZ":
                    return "p2"
                elif event['Winner'] == "FaZe":
                    return "p1"
            elif event['Status'] in ["Canceled", "Postponed"]:
                return "p3"
    return "p3"  # Default to 50-50 if no conclusive data

# Main function to execute the program logic
def main():
    match_date = datetime.strptime("2025-06-12", "%Y-%m-%d").date()
    path = f"GamesByDate/{match_date}"
    data = make_request(PROXY_ENDPOINT, path)
    result = determine_outcome(data)
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()