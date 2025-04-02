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
        # Fetch data
        briefings = fetch_press_briefings()
        
        # Define the terms to search for
        terms = ["AI", "artificial intelligence", "AIs", "artificial intelligences"]
        
        # Check for the occurrence of the terms
        mentioned = any(check_for_term(briefings, term) for term in terms)
        
        # Determine the recommendation based on the findings
        if mentioned:
            print("recommendation: p2")  # Yes
        else:
            print("recommendation: p1")  # No
    except Exception as e:
        print(f"An error occurred: {e}")
        print("recommendation: p3")  # Unknown/50-50 due to error

if __name__ == "__main__":
    main()