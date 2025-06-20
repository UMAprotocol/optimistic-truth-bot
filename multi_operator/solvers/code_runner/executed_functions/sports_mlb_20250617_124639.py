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
def determine_outcome(games):
    for game in games:
        if PLAYER1 in game['Players'] and PLAYER2 in game['Players']:
            if game['Winner'] == PLAYER1:
                return "p2"  # De Minaur wins
            elif game['Winner'] == PLAYER2:
                return "p1"  # Lehecka wins
            else:
                return "p3"  # Tie or undetermined
    return "p3"  # No game found or no winner determined

# Main function to process the match data
def process_match():
    current_date = datetime.now().strftime("%Y-%m-%d")
    if current_date > END_DATE:
        return "p3"  # Resolve as 50-50 if the date is beyond the end date

    games = fetch_data(HSBC_CHAMPIONSHIPS_URL.format(date=MATCH_DATE))
    if not games:
        return "p3"  # Resolve as 50-50 if no data is available

    return determine_outcome(games)

# Run the main function and print the recommendation
if __name__ == "__main__":
    recommendation = process_match()
    print(f"recommendation: {recommendation}")