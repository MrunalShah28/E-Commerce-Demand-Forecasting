import datetime
import random

def _generate_fallback(keyword="running shoes", days=60):
    """Deterministic-ish fallback when Google Trends is unavailable."""
    data = []
    base_trend = 55
    today = datetime.date.today()
    random.seed(42)
    for i in range(days, 0, -1):
        d = today - datetime.timedelta(days=i)
        base_trend = max(10, min(100, base_trend + random.gauss(0, 5)))
        data.append({
            "date":         str(d),
            "search_trend": int(base_trend),
        })
    return data


def get_trend_data(keyword="running shoes"):
    try:
        from pytrends.request import TrendReq

        pytrends = TrendReq(hl="en-US", tz=330)
        pytrends.build_payload([keyword], timeframe="today 3-m")

        df = pytrends.interest_over_time()
        if df.empty:
            raise ValueError("Empty response from Google Trends")

        df = df.reset_index()
        result = []
        for _, row in df.tail(60).iterrows():
            result.append({
                "date":         str(row["date"])[:10],
                "search_trend": int(row[keyword]),
            })
        return result

    except Exception as e:
        print(f"[trends] Warning: Google Trends unavailable ({e}). Using fallback data.")
        return _generate_fallback(keyword)
