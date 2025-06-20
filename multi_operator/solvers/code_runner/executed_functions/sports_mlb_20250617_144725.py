import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# Constants
DATE = "2025-06-17"
PLAYER1 = "Ugo Humbert"
PLAYER2 = "Denis Shapovalov"
TOURNAMENT = "Terra Wortmann Open"
MATCH_STATUS_URL = "https://www.terrawortmann-open.de/en/"

# Headers for API requests
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

def get_match_result():
    try:
        # Simulating API call to get match result
        response = requests.get(MATCH_STATUS_URL, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            # This is a placeholder for actual data parsing logic
            match_data = response.json()
            for match in match_data:
                if (match['player1'] == PLAYER1 and match['player2'] == PLAYER2 and
                    match['date'].startswith(DATE) and match['tournament'] == TOURNAMENT):
                    if match['winner'] == PLAYER1:
                        return "p2"  # Humbert wins
                    elif match['winner'] == PLAYER2:
                        return "p1"  # Shapovalov wins
                    else:
                        return "p3"  # Match tie, canceled, or delayed
        else:
            print(f"Failed to fetch data: {response.status_code}")
            return "p3"  # Assume 50-50 if data fetch fails
    except requests.RequestException as e:
        print(f"Error during requests to {MATCH_STATUS_URL}: {str(e)}")
        return "p3"  # Assume 50-50 on error

if __name__ == "__main__":
    # Check if the current date is past the match date
    current_date = datetime.now()
    match_date = datetime.strptime(DATE + " 07:00", "%Y-%m-%d %H:%M")
    if current_date > match_date + timedelta(days=7):
        result = get_match_result()
    else:
        result = "p4"  # Too early to resolve

    print("recommendation:", result)