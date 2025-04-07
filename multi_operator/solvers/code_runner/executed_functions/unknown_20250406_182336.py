import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Constants
SPORTS_DATA_IO_API_KEY = os.getenv('SPORTS_DATA_IO_MLB_API_KEY')
SPORTS_DATA_IO_URL = "https://api.sportsdata.io/v3/cricket/scores/json/Match/{match_id}"

# Match and date details
match_date = "2025-04-05"
match_teams = ("Punjab Kings", "Rajasthan Royals")
deadline_date = "2025-04-12 23:59:59"

def fetch_match_id():
    # This function should ideally fetch the match ID from the API using team names and date
    # Here we assume a placeholder function due to lack of specific API endpoint details
    return "12345"  # Placeholder match ID

def fetch_match_result(match_id):
    headers = {'Ocp-Apim-Subscription-Key': SPORTS_DATA_IO_API_KEY}
    response = requests.get(SPORTS_DATA_IO_URL.format(match_id=match_id), headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception("Failed to fetch match data")

def resolve_market(match_data):
    current_time = datetime.now()
    match_completion_time = datetime.strptime(match_data.get('MatchCompletedDateTime'), '%Y-%m-%dT%H:%M:%S')
    deadline = datetime.strptime(deadline_date, '%Y-%m-%d %H:%M:%S')

    if match_completion_time > deadline:
        return "recommendation: p3"  # Market resolves 50-50
    elif match_data.get('Winner') == "Punjab Kings":
        return "recommendation: p2"  # Punjab wins
    elif match_data.get('Winner') == "Rajasthan Royals":
        return "recommendation: p1"  # Rajasthan wins
    else:
        return "recommendation: p3"  # In case of draw or no result

def main():
    try:
        match_id = fetch_match_id()
        match_data = fetch_match_result(match_id)
        result = resolve_market(match_data)
        print(result)
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()