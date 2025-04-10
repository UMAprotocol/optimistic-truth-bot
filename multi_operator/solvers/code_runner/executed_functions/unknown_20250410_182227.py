import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Constants
NASA_DATA_URL = "https://data.giss.nasa.gov/gistemp/tabledata_v4/GLB.Ts+dSST.txt"
DEADLINE_DATE = "2025-07-01T23:59:00"

def fetch_temperature_data(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

def parse_temperature_data(data):
    if data is None:
        return None
    lines = data.split('\n')
    march_temperatures = {}
    for line in lines:
        if line.startswith('Year'):
            continue
        parts = line.split()
        if len(parts) >= 4:
            year = parts[0]
            march_temp = parts[3]
            if march_temp != '****':
                march_temperatures[year] = float(march_temp)
    return march_temperatures

def determine_hottest_march(temperatures):
    if temperatures is None:
        return "p3"  # Unknown
    max_temp = max(temperatures.values())
    march_2025_temp = temperatures.get("2025", None)
    if march_2025_temp is None:
        return "p3"  # Unknown
    if march_2025_temp > max_temp:
        return "p2"  # Yes
    else:
        return "p1"  # No

def main():
    # Fetch and parse data
    raw_data = fetch_temperature_data(NASA_DATA_URL)
    temperatures = parse_temperature_data(raw_data)
    
    # Determine if March 2025 is the hottest on record
    result = determine_hottest_march(temperatures)
    
    # Output the result
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()