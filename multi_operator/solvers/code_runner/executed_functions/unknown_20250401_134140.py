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
    """Fetches data from a hypothetical API that provides transcripts of White House press briefings."""
    params = {
        'api_key': API_KEY,
        'date': '03122025',  # Date of the next briefing as per the user's question
        'speaker': 'Karoline Leavitt'
    }
    response = requests.get(WHITE_HOUSE_PRESS_BRIEFING_API_URL, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to fetch data: {response.status_code} - {response.text}")

def count_occurrences(text, term):
    """Counts occurrences of the term in the given text, considering pluralization and possessive forms."""
    words = text.split()
    count = 0
    for word in words:
        if word.lower() in [term.lower(), term.lower()+'s', term.lower()+'\'s']:
            count += 1
    return count

def analyze_data():
    """Analyzes the fetched data to determine if the term 'President' was said 60+ times."""
    try:
        data = fetch_press_briefing_data()
        transcripts = data.get('transcripts', [])
        total_count = 0
        for transcript in transcripts:
            total_count += count_occurrences(transcript['text'], 'President')
        
        if total_count >= 60:
            return 'recommendation: p2'  # Corresponds to "Yes"
        else:
            return 'recommendation: p1'  # Corresponds to "No"
    except Exception as e:
        print(f"Error during analysis: {str(e)}")
        return 'recommendation: p3'  # Corresponds to unknown/50-50 if there's an error

# Main execution
if __name__ == "__main__":
    result = analyze_data()
    print(result)