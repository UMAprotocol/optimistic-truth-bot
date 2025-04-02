import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Constants
WHITE_HOUSE_PRESS_BRIEFING_API_URL = "https://api.example.com/whitehouse/pressbriefings"
API_KEY = os.getenv('API_KEY')  # Assuming a generic API key for demonstration

def fetch_press_briefings():
    """Fetches press briefings data from an API."""
    headers = {'Authorization': f'Bearer {API_KEY}'}
    response = requests.get(WHITE_HOUSE_PRESS_BRIEFING_API_URL, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to fetch data: {response.status_code} - {response.text}")

def check_for_common_sense(briefings):
    """Checks if 'common sense' is mentioned in the briefings."""
    for briefing in briefings:
        if 'common sense' in briefing['transcript'].lower():
            return True
    return False

def main():
    try:
        # Fetch data
        briefings = fetch_press_briefings()
        
        # Check for the term "common sense"
        if check_for_common_sense(briefings):
            print("recommendation: p2")  # p2 corresponds to Yes
        else:
            print("recommendation: p1")  # p1 corresponds to No

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        print("recommendation: p3")  # p3 corresponds to unknown/50-50

if __name__ == "__main__":
    main()