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

def check_for_common_sense_statements(transcript):
    """Checks if 'Common Sense' or its variations are mentioned in the transcript."""
    terms = ["common sense", "common senses", "common sense's"]
    for term in terms:
        if term in transcript.lower():
            return True
    return False

def main():
    try:
        data = fetch_press_briefing_data()
        for briefing in data.get('briefings', []):
            date_of_briefing = datetime.strptime(briefing['date'], '%Y-%m-%d')
            if date_of_briefing > datetime.now():
                continue  # Skip future briefings
            if 'Karoline Leavitt' in briefing['participants']:
                if check_for_common_sense_statements(briefing['transcript']):
                    print('recommendation: p2')  # Yes, she said "Common Sense"
                    return
        # If no briefing found with the term or no briefing yet
        print('recommendation: p1')  # No, she did not say "Common Sense"
    except Exception as e:
        print(f"Error occurred: {e}")
        print('recommendation: p3')  # Unknown/50-50 due to error

if __name__ == "__main__":
    main()