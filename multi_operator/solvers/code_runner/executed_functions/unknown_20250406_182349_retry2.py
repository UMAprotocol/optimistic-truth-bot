import os
import requests
from datetime import datetime
from dotenv import load_dotenv

def fetch_match_result():
    load_dotenv()
    api_key = os.getenv('SPORTS_DATA_IO_MLB_API_KEY')
    url = f"https://api.sportsdata.io/v3/cricket/scores/json/Match/{match_id}?key={api_key}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        return None

def resolve_market(match_data):
    current_time = datetime.utcnow()
    match_end_time = datetime.strptime('2025-04-12 23:59:59', '%Y-%m-%d %H:%M:%S')
    if current_time > match_end_time:
        return "recommendation: p3"  # 50-50 outcome
    if not match_data:
        return "recommendation: p4"  # Too early to resolve
    if match_data['Status'] != 'Final':
        return "recommendation: p4"  # Match not completed
    winner = match_data['Winner']
    if winner == 'Punjab Kings':
        return "recommendation: p2"  # Punjab wins
    elif winner == 'Rajasthan Royals':
        return "recommendation: p1"  # Rajasthan wins
    else:
        return "recommendation: p3"  # 50-50 outcome

if __name__ == "__main__":
    match_id = '12345'  # Example match ID, replace with actual match ID
    match_data = fetch_match_result()
    recommendation = resolve_market(match_data)
    print(recommendation)