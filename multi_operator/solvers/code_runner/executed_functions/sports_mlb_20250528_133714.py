import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_MLB_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_MLB_API_KEY")

# Configuration for headers
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}

# Function to make GET requests
def get_request(url, headers):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error during requests to {url}: {str(e)}")
        return None

# Function to check if Casper Ruud reached the quarterfinals
def check_ruud_quarterfinals():
    current_year = datetime.now().year
    url = f"https://api.sportsdata.io/v3/tennis/scores/json/PlayerTournamentStatsByPlayer/{current_year}/roland-garros/Casper-Ruud"
    data = get_request(url, HEADERS)
    
    if data:
        for record in data:
            if record.get("Round") and "Quarterfinals" in record.get("Round"):
                return "recommendation: p2"  # Yes, reached the quarterfinals
        return "recommendation: p1"  # No, did not reach the quarterfinals
    else:
        return "recommendation: p3"  # Unknown or API error

# Main execution
if __name__ == "__main__":
    result = check_ruud_quarterfinals()
    print(result)