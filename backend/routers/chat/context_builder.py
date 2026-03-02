
import time                 # Used to get current time (for caching system)
import pandas as pd         # Pandas is used to work with table-like data (DataFrames)

# Import database connection function from your core module
from core.database import get_db_connection

# Import function that resamples stock data (e.g., 1D, 1W, 1M, 1Y)
from routers.analysis import resample_data

# Import prediction function (LSTM model prediction)
from routers.predictions import predict

# Import technical indicator calculation function
from routers.technical_status import technical_status


# Dictionary used to temporarily store stock context data (cache memory)
_CONTEXT_CACHE = {}

# Time-to-live for cache (in seconds)
# This means cached data is valid for 60 seconds
CACHE_TTL_SECONDS = 60


def build_stock_context(symbol: str, timeframe: str = "1Y"):
    """
    This function builds and returns stock analysis context
    including:
    - Latest price
    - Technical indicators (RSI, EMA, Bollinger Bands)
    - Prediction from ML model
    - Technical status summary
    """

    # Convert symbol to uppercase and remove extra spaces
    # Example: " aapl " → "AAPL"
    sym = symbol.upper().strip()

    # Create a unique cache key using symbol + timeframe
    # Example: ("AAPL", "1Y")
    key = (sym, timeframe)

    # Get current timestamp
    now = time.time()

    # ------------------------------
    # 🔹 CHECK CACHE FIRST
    # ------------------------------

    # If this symbol + timeframe exists in cache
    if key in _CONTEXT_CACHE:

        # Retrieve stored timestamp and cached data
        ts, cached = _CONTEXT_CACHE[key]

        # If cached data is still valid (not older than 60 seconds)
        if now - ts < CACHE_TTL_SECONDS:
            return cached   # Return cached result immediately (very fast)

    # ------------------------------
    # 🔹 FETCH DATA FROM DATABASE
    # ------------------------------

    # Open database connection
    conn = get_db_connection()

    # Read stock data using SQL query
    df = pd.read_sql(
        """
        SELECT date, symbol, open, high, low, close, close_norm
        FROM stocks
        WHERE symbol=%s
        ORDER BY date ASC
        """,
        conn,
        params=(sym,)   # Prevents SQL injection (safe query)
    )

    # Close database connection (important!)
    conn.close()

    # If no data found, return None
    if df.empty:
        return None

    # ------------------------------
    # 🔹 RESAMPLE DATA
    # ------------------------------

    # Resample data based on timeframe
    # Example:
    # "1Y" → last 1 year
    # "1M" → last 1 month
    # Also calculates indicators like:
    # RSI14, EMA12, EMA26, Bollinger Bands
    df = resample_data(df, timeframe)

    # Get the latest row (most recent date)
    latest = df.iloc[-1]

    # ------------------------------
    # 🔹 GET AI PREDICTION
    # ------------------------------

    # Call LSTM prediction function
    # This is cached internally so it is fast
    pred = predict(sym)

    # ------------------------------
    # 🔹 GET TECHNICAL STATUS
    # ------------------------------

    # Calculate overall technical summary
    # Example: "Bullish", "Bearish", etc.
    tech = technical_status(sym)

    # ------------------------------
    # 🔹 BUILD CONTEXT DICTIONARY
    # ------------------------------

    # Create dictionary containing everything needed
    ctx = {
        "symbol": sym,                           # Stock symbol
        "price": float(latest["close"]),         # Latest closing price
        "rsi": float(latest["RSI14"]),           # RSI indicator
        "ema12": float(latest["EMA12"]),         # 12-period EMA
        "ema26": float(latest["EMA26"]),         # 26-period EMA
        "bb_upper": float(latest["BB_UPPER"]),   # Bollinger Upper Band
        "bb_lower": float(latest["BB_LOWER"]),   # Bollinger Lower Band
        "prediction": pred,                      # ML prediction result
        "technical": tech,                       # Technical analysis summary
    }

    # ------------------------------
    # 🔹 STORE RESULT IN CACHE
    # ------------------------------

    # Save result with timestamp
    _CONTEXT_CACHE[key] = (now, ctx)

    # Return final stock context
    return ctx