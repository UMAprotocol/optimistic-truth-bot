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
    lines = data.split('\n')
    march_temperatures = {}
    for line in lines:
        if line.strip() and line[0].isdigit():
            parts = line.split()
            year = int(parts[0])
            march_temp = float(parts[3])  # March is the 4th column (index 3)
            march_temperatures[year] = march_temp
    return march_temperatures

def determine_hottest_march(march_temperatures, target_year=2025):
    target_temp = march_temperatures.get(target_year)
    if target_temp is None:
        return "p4"  # Data for 2025 is not available yet
    for year, temp in march_temperatures.items():
        if year != target_year and temp >= target_temp:
            return "p1"  # Found a year with a temperature equal or higher
    return "p2"  # No year was hotter

def main():
    data = fetch_temperature_data()
    if data:
        march_temperatures = parse_temperature_data(data)
        recommendation = determine_hottest_march(march_temperatures)
        print(f"recommendation: {recommendation}")
    else:
        print("recommendation: p4")  # Unable to fetch or parse data

if __name__ == "__main__":
    main()