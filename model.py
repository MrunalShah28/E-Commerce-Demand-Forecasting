import pandas as pd
import numpy as np
from xgboost import XGBRegressor

# -------------------------------
# Feature Engineering
# -------------------------------
def create_features(df):
    df = df.copy()
    df["day_of_week"] = df.index.dayofweek
    df["month"]       = df.index.month

    # Lag features
    df["sales_lag_7"]  = df["sales"].shift(7)
    df["sales_lag_14"] = df["sales"].shift(14)
    df["trend_lag_7"]  = df["search_trend"].shift(7)
    df["trend_lag_14"] = df["search_trend"].shift(14)

    # Trend momentum
    df["trend_momentum"] = df["search_trend"].pct_change()

    df = df.dropna()
    return df


# -------------------------------
# Anomaly Detection
# -------------------------------
def detect_anomalies(trend_data, z_thresh=2.0):
    """
    Returns a list of anomaly dicts for the frontend.
    Uses Z-score on search_trend values.
    """
    if not trend_data:
        return []

    df = pd.DataFrame(trend_data)
    mean = df["search_trend"].mean()
    std  = df["search_trend"].std()
    if std == 0:
        return []

    anomalies = []
    for _, row in df.iterrows():
        z = round((row["search_trend"] - mean) / std, 2)
        if abs(z) >= z_thresh:
            severity = "CRITICAL" if abs(z) >= 3 else ("HIGH" if abs(z) >= 2.5 else "MEDIUM")
            anomalies.append({
                "date":         row["date"],
                "search_trend": int(row["search_trend"]),
                "z_score":      z,
                "severity":     severity,
                "sales":        int(row["search_trend"] * 0.7),  # proxy until real sales
            })

    return anomalies


# -------------------------------
# Main Prediction Function
# -------------------------------
def predict_demand(trend_data):
    """
    Returns:
      - predictions dict  { "7_day": int, "14_day": int, "30_day": int }
      - forecast_series   list of { date, ensemble, xgboost } for the next 30 days
    """
    df = pd.DataFrame(trend_data)

    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
        df.set_index("date", inplace=True)

    # Rename trend column
    trend_col = [col for col in df.columns if col != "date"][0]
    df.rename(columns={trend_col: "search_trend"}, inplace=True)

    # Simulate sales until real sales data exists
    np.random.seed(42)
    df["sales"] = df["search_trend"] * 0.7 + np.random.normal(5, 2, len(df))

    df = create_features(df)

    features = [col for col in df.columns if col != "sales"]
    X = df[features]
    y = df["sales"]

    model = XGBRegressor(n_estimators=100, max_depth=5, random_state=42)
    model.fit(X, y)

    # ── Multi-horizon scalar forecasts ──
    last_data = df.tail(30)
    forecast_7  = model.predict(last_data.tail(7)[features]).mean()
    forecast_14 = model.predict(last_data.tail(14)[features]).mean()
    forecast_30 = model.predict(last_data.tail(30)[features]).mean()

    predictions = {
        "7_day":  int(forecast_7),
        "14_day": int(forecast_14),
        "30_day": int(forecast_30),
    }

    # ── 30-day daily forecast series (for the chart) ──
    last_row = df.tail(1).copy()
    base_sales = float(last_row["sales"].iloc[0])
    base_trend = float(last_row["search_trend"].iloc[0])

    forecast_series = []
    for i in range(1, 31):
        future_date = pd.Timestamp.today().normalize() + pd.Timedelta(days=i)
        row = last_row.copy()
        row.index = [future_date]

        # Simulate slight drift in trend & lag features
        row["search_trend"] = max(10, min(100, base_trend + np.random.normal(0, 3)))
        row["day_of_week"]  = future_date.dayofweek
        row["month"]        = future_date.month
        row["sales_lag_7"]  = base_sales
        row["sales_lag_14"] = base_sales
        row["trend_lag_7"]  = base_trend
        row["trend_lag_14"] = base_trend
        row["trend_momentum"] = 0.0

        pred_val = float(model.predict(row[features])[0])
        # Slight random noise for ensemble spread
        forecast_series.append({
            "date":     future_date.strftime("%Y-%m-%d"),
            "xgboost":  round(pred_val, 1),
            "ensemble": round(pred_val * 0.95 + np.random.normal(0, 2), 1),
        })

    return predictions, forecast_series
