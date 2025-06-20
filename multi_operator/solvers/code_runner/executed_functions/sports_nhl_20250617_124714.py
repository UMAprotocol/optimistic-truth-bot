import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# Constants
HSBC_CHAMPIONSHIPS_URL = "https://api.sportsdata.io/v3/tennis/scores/json/GamesByDate/{date}"
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
MATCH_DATE = "2025-06-17"
END_DATE = "2025-06-24"
PLAYER1 = "Alex De Minaur"
PLAYER2 = "Jiri Lehecka"

# Function to fetch data from API
def fetch_data(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

# Function to determine the outcome of the match
def determine_outcome(matches):
    for match in matches:
        if PLAYER1 in match['Players'] and PLAYER2 in match['Players']:
            if match['Winner'] == PLAYER1:
                return "recommendation: p2"  # De Minaur wins
            elif match['Winner'] == PLAYER2:
                return "recommendation: p1"  # Lehecka wins
            else:
                return "recommendation: p3"  # Match tie or other issues
    return "recommendation: p3"  # No match found or other issues

# Main function to process the match data
def process_match():
    current_date = datetime.now().strftime("%Y-%m-%d")
    if current_date > END_DATE:
        return "recommendation: p3"  # Resolve as 50-50 if beyond end date

    match_date_formatted = datetime.strptime(MATCH_DATE, "%Y-%m-%d").strftime("%Y-%m-%d")
    url = HSBC_CHAMPIONSHIPS_URL.format(date=match_date_formatted)
    matches = fetch_data(url)

    if matches is None:
        return "recommendation: p3"  # Unable to fetch data, resolve as 50-50

    return determine_outcome(matches)

# Run the main function
if __name__ == "__main__":
    result = process_match()
    print(result)