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

def check_for_phrase(briefings, phrase):
    """Checks if the phrase is mentioned in the briefings."""
    for briefing in briefings:
        if phrase in briefing['transcript']:
            return True
    return False

def main():
    try:
        # Define the phrase to look for and the deadline
        phrase = "Go ahead"
        deadline = datetime.strptime("2025-12-31 23:59", "%Y-%m-%d %H:%M")
        
        # Check if current date is past the deadline
        if datetime.now() > deadline:
            print("recommendation: p1")  # Market resolves to "No" after deadline
            return
        
        # Fetch press briefings
        briefings = fetch_press_briefings()
        
        # Check for the phrase in the briefings
        if check_for_phrase(briefings, phrase):
            print("recommendation: p2")  # Phrase found, resolves to "Yes"
        else:
            print("recommendation: p1")  # Phrase not found, resolves to "No"
    
    except Exception as e:
        print(f"An error occurred: {e}")
        print("recommendation: p3")  # Unknown/50-50 if an error occurs

if __name__ == "__main__":
    main()