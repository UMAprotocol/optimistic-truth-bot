import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Constants
WHITE_HOUSE_PRESS_BRIEFING_API_URL = "https://api.example.com/whitehouse/pressbriefings"
API_KEY = os.getenv('API_KEY')  # Assuming a generic API key for demonstration

def fetch_press_briefing_data():
    """Fetches the latest White House press briefing data."""
    headers = {'Authorization': f'Bearer {API_KEY}'}
    response = requests.get(WHITE_HOUSE_PRESS_BRIEFING_API_URL, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to fetch data: {response.status_code} - {response.text}")

def count_occurrences(transcript, term):
    """Counts the occurrences of a term in the transcript."""
    return transcript.lower().count(term.lower())

def analyze_briefing(briefings, term="Go ahead"):
    """Analyzes the briefings to determine if the term was said 3+ times."""
    for briefing in briefings:
        if 'transcript' in briefing:
            count = count_occurrences(briefing['transcript'], term)
            if count >= 3:
                return True
    return False

def main():
    try:
        briefings = fetch_press_briefing_data()
        result = analyze_briefing(briefings)
        if result:
            print("recommendation: p2")  # Corresponds to "Yes"
        else:
            print("recommendation: p1")  # Corresponds to "No"
    except Exception as e:
        print(f"Error: {str(e)}")
        print("recommendation: p3")  # Corresponds to unknown/50-50 if there's an error

if __name__ == "__main__":
    main()