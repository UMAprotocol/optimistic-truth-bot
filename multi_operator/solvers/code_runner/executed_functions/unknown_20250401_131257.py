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

def check_for_term(briefings, term):
    """Checks if the term is mentioned in the briefings."""
    for briefing in briefings:
        if term in briefing['transcript']:
            return True
    return False

def main():
    try:
        # Define the term to search for and the deadline
        term_to_search = "Saudi"
        deadline = datetime.strptime("2025-12-31 23:59", "%Y-%m-%d %H:%M")
        
        # Fetch press briefings
        briefings = fetch_press_briefings()
        
        # Check if the term is mentioned in any of the briefings
        term_found = check_for_term(briefings, term_to_search)
        
        # Check if current date is past the deadline
        if datetime.now() > deadline:
            if term_found:
                print("recommendation: p2")  # Term found, resolve to Yes
            else:
                print("recommendation: p1")  # Term not found and past deadline, resolve to No
        else:
            if term_found:
                print("recommendation: p2")  # Term found, resolve to Yes
            else:
                print("recommendation: p3")  # Still within deadline, unknown if term will be mentioned later
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        print("recommendation: p3")  # Resolve to unknown/50-50 in case of error

if __name__ == "__main__":
    main()