from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from trends import get_trend_data
from scraper import get_product_data
from model import predict_demand, detect_anomalies
import os

app = FastAPI(title="IntentDemand API", version="2.0")

# ── CORS (allow the frontend to call the API) ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Serve the dashboard HTML at root ──
STATIC_DIR = os.path.dirname(os.path.abspath(__file__))

@app.get("/")
def serve_dashboard():
    return FileResponse(os.path.join(STATIC_DIR, "demand_dashboard.html"))

@app.get("/data")
def get_data():
    trend_data  = get_trend_data()
    product_data = get_product_data()
    predictions, forecast_series = predict_demand(trend_data)
    anomalies   = detect_anomalies(trend_data)

    # Inventory decision logic
    pred_7d = predictions.get("7_day", 0)
    has_anomaly = len(anomalies) > 0

    if pred_7d > 50 and has_anomaly:
        inventory = "URGENT"
    elif pred_7d > 30:
        inventory = "MODERATE"
    else:
        inventory = "NORMAL"

    return {
        "trend":      trend_data,
        "products":   product_data,
        "forecast":   predictions,
        "forecast_series": forecast_series,
        "anomalies":  anomalies,
        "inventory":  inventory,
    }
