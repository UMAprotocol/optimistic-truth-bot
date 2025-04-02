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

def check_for_term(briefings, term="astronaut"):
    """Checks if the term is mentioned in the press briefings."""
    for briefing in briefings:
        transcript = briefing.get('transcript', '')
        if term in transcript:
            return True
    return False

def main():
    try:
        # Fetch data
        briefings = fetch_press_briefings()
        
        # Check for the term "astronaut"
        term_found = check_for_term(briefings)
        
        # Determine the recommendation based on the presence of the term
        recommendation = 'p2' if term_found else 'p1'
        
        # Print the recommendation
        print(f'recommendation: {recommendation}')
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        print('recommendation: p3')  # Unknown/50-50 if an error occurs

if __name__ == "__main__":
    main()