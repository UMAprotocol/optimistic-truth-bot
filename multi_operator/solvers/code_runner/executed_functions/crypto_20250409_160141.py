import requests
from datetime import datetime
import pytz

def fetch_binance_price(date_str, symbol="ETHUSDT"):
    """Fetch the closing price of a cryptocurrency from Binance at a specific minute."""
    base_url = "https://api.binance.com/api/v3/klines"
    params = {
        "symbol": symbol,
        "interval": "1m",
        "startTime": int(datetime.strptime(date_str, "%Y-%m-%d %H:%M").replace(tzinfo=pytz.timezone("America/New_York")).timestamp() * 1000),
        "endTime": int(datetime.strptime(date_str, "%Y-%m-%d %H:%M").replace(tzinfo=pytz.timezone("America/New_York")).timestamp() * 1000) + 60000
    }
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()
        if data and len(data) > 0:
            return float(data[0][4])  # Close price
        else:
            return None
    except requests.RequestException as e:
        print(f"Error fetching data from Binance: {e}")
        return None

def resolve_market():
    price_april_8 = fetch_binance_price("2025-04-08 12:00")
    price_april_9 = fetch_binance_price("2025-04-09 12:00")

    if price_april_8 is None or price_april_9 is None:
        print("Failed to fetch prices. Cannot resolve market.")
        return "recommendation: p4"

    if price_april_8 < price_april_9:
        return "recommendation: p2"  # Up
    elif price_april_8 > price_april_9:
        return "recommendation: p1"  # Down
    else:
        return "recommendation: p3"  # 50-50

# Run the resolution function and print the result
print(resolve_market())