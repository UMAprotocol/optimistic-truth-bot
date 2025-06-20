import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("SPORTS_DATA_IO_NHL_API_KEY")
if not API_KEY:
    raise ValueError("Missing SPORTS_DATA_IO_NHL_API_KEY")

# Constants
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY}
RESOLUTION_MAP = {
    "EDM": "p2",  # Edmonton Oilers
    "LAK": "p1",  # Los Angeles Kings
    "50-50": "p3",
    "Too early to resolve": "p4",
}
CUTOFF_DATE = "2025-05-20T23:59:00"

# Helper functions
def get_json_response(url, headers):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

def check_series_status():
    current_date = datetime.utcnow().isoformat()
    if current_date > CUTOFF_DATE:
        return "50-50"
    
    url = "https://api.sportsdata.io/v3/nhl/scores/json/PlayoffSeries"
    series_data = get_json_response(url, HEADERS)
    if series_data:
        for series in series_data:
            if series['Round'] == 1 and {'EDM', 'LAK'} <= set([series['AwayTeam'], series['HomeTeam']]):
                if series['Status'] == "Completed":
                    winner = series['Winner']
                    return RESOLUTION_MAP.get(winner, "Too early to resolve")
                elif series['Status'] in ["Canceled", "Postponed"]:
                    return "50-50"
    return "Too early to resolve"

# Main execution
if __name__ == "__main__":
    result = check_series_status()
    print("recommendation:", RESOLUTION_MAP.get(result, "Too early to resolve"))