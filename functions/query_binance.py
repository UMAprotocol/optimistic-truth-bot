import requests
from datetime import datetime, timedelta, timezone
import pytz

def get_close_price_at_et_noon(date_str):
    """
    Fetches the 1-minute candle close price for BTCUSDT on Binance
    at 12:00 PM US Eastern Time on a given date (format: 'YYYY-MM-DD').
    """
    et = pytz.timezone('US/Eastern')
    target_time_et = et.localize(datetime.strptime(date_str + ' 12:00:00', '%Y-%m-%d %H:%M:%S'))
    target_time_utc = target_time_et.astimezone(timezone.utc)
    start_time_ms = int(target_time_utc.timestamp() * 1000)

    params = {
        'symbol': 'BTCUSDT',
        'interval': '1m',
        'limit': 1,
        'startTime': start_time_ms,
        'endTime': start_time_ms + 60_000  # plus 1 minute
    }

    response = requests.get("https://api.binance.com/api/v3/klines", params=params)
    data = response.json()
    
    if not data:
        raise Exception(f"No data returned for {date_str} 12:00 PM ET")

    close_price = float(data[0][4])
    return close_price

# Fetch prices
price_29 = get_close_price_at_et_noon('2025-03-29')
price_30 = get_close_price_at_et_noon('2025-03-30')

print(f"Close price on Mar 29, 12:00 ET: {price_29}")
print(f"Close price on Mar 30, 12:00 ET: {price_30}")

# Resolution logic
if price_30 > price_29:
    print("recommendation: p2")  # Up
elif price_30 < price_29:
    print("recommendation: p1")  # Down
else:
    print("recommendation: p3")  # 50-50