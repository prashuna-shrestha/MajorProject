from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
import pandas as pd
import math
import numpy as np

app = FastAPI()

# --- CORS setup ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Database configuration ---
DB_CONFIG = {
    "dbname": "stock_data",
    "user": "postgres",
    "password": "prashuna123",
    "host": "localhost",
    "port": "5433",
}

# --- Helper: clean NaN/Inf for JSON ---
def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    df = df.replace([np.inf, -np.inf], None)
    df = df.where(pd.notnull(df), None)
    return df

# --- Fetch stock data ---
def get_stock_data(symbol: str) -> pd.DataFrame:
    conn = psycopg2.connect(**DB_CONFIG)
    query = """
        SELECT date, symbol, open, high, low, close, close_norm
        FROM stocks
        WHERE LOWER(symbol) = LOWER(%s)
        ORDER BY date ASC
    """
    df = pd.read_sql(query, conn, params=(symbol,))
    conn.close()
    return df

# --- Resample and trend analysis ---
def resample_data(df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")
    df.set_index("date", inplace=True)

    # Define lookback windows
    days_map = {
        "1D": 1,
        "1W": 7,
        "1M": 30,
        "6M": 180,
        "1Y": 365,
        "3Y": 1095,
        "5Y": 1825,
        "ALL": None,
    }

    # Handle timeframe safely
    if timeframe in ["1W", "1M"]:
        rule = "W" if timeframe == "1W" else "M"
        df_resampled = df.resample(rule).agg({
            "open": "first",
            "high": "max",
            "low": "min",
            "close": "last"
        })
    elif timeframe in days_map and days_map[timeframe]:
        df_resampled = df.tail(days_map[timeframe])
    else:
        df_resampled = df.copy()

    # --- Trend metrics ---
    df_resampled["avg_price"] = (df_resampled["high"] + df_resampled["low"]) / 2
    df_resampled["price_change"] = df_resampled["close"].pct_change(fill_method=None) * 100
    df_resampled["price_change"] = df_resampled["price_change"].replace([np.inf, -np.inf, np.nan], 0)
    df_resampled["rolling_mean_20"] = df_resampled["close"].rolling(window=20, min_periods=1).mean()

    df_resampled.reset_index(inplace=True)
    df_resampled = clean_dataframe(df_resampled)

    return df_resampled

# --- API endpoint ---
@app.get("/api/stocks")
def get_stock(symbol: str = "NEPSE", timeframe: str = "1Y"):
    df = get_stock_data(symbol)
    if df.empty:
        return []
    df_filtered = resample_data(df, timeframe)
    return df_filtered.to_dict(orient="records")
