import requests
from datetime import datetime

def fetch_temperature_data():
    url = "https://data.giss.nasa.gov/gistemp/tabledata_v4/GLB.Ts+dSST.txt"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except requests.exceptions.HTTPError as err:
        print(f"HTTP error occurred: {err}")
    except Exception as err:
        print(f"An error occurred: {err}")
    return None

def parse_temperature_data(data):
    if data is None:
        return None, None
    lines = data.splitlines()
    year_data = {}
    for line in lines:
        if line.startswith("Year"):
            continue
        parts = line.split()
        if len(parts) >= 4:
            year = parts[0]
            march_temp = parts[3]
            if march_temp != "****":
                year_data[int(year)] = float(march_temp)
    return year_data

def determine_hottest_march(year_data):
    if year_data is None:
        return "p4"
    current_year = datetime.now().year
    if 2025 not in year_data or current_year < 2025:
        return "p4"
    max_temp = max(year_data.values())
    if year_data[2025] > max_temp:
        return "p2"
    return "p1"

def main():
    data = fetch_temperature_data()
    year_data = parse_temperature_data(data)
    recommendation = determine_hottest_march(year_data)
    print(f"recommendation: {recommendation}")

if __name__ == "__main__":
    main()