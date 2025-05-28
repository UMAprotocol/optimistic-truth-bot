import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API keys loaded from environment variables
ROLAND_GARROS_API_KEY = os.getenv("SPORTS_DATA_IO_CBB_API_KEY")  # Assuming tennis data is under CBB for this example

# API endpoints
PRIMARY_ENDPOINT = "https://api.sportsdata.io/v3/cbb/scores/json"
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/cbb-proxy"

# Headers for API requests
HEADERS = {"Ocp-Apim-Subscription-Key": ROLAND_GARROS_API_KEY}

# Function to make API requests
def make_request(endpoint, path):
    url = f"{endpoint}/{path}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

# Function to check if Grigor Dimitrov reached the quarterfinals
def check_quarterfinals():
    # Construct the path for the current year's tournament results
    current_year = datetime.now().year
    path = f"Tournaments/{current_year}/PlayerResults/GrigorDimitrov"

    # Try proxy endpoint first
    data = make_request(PROXY_ENDPOINT, path)
    if data is None:
        # Fallback to primary endpoint if proxy fails
        data = make_request(PRIMARY_ENDPOINT, path)

    # Analyze the data to determine if the player reached the quarterfinals
    if data:
        for result in data:
            if result.get('Round') == 'Quarterfinals' and result.get('Player') == 'Grigor Dimitrov':
                return "recommendation: p2"  # Yes, reached quarterfinals
        return "recommendation: p1"  # No, did not reach quarterfinals
    else:
        return "recommendation: p3"  # Unknown/50-50 if data retrieval failed

# Main execution
if __name__ == "__main__":
    result = check_quarterfinals()
    print(result)