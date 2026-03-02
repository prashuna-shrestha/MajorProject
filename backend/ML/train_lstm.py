# ===================================================
# 1. System Imports
# ===================================================
import sys
import os

# Make backend folder discoverable
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(BASE_DIR)
sys.path.append(PARENT_DIR)


# ===================================================
# 2. Library Imports
# ===================================================
import pandas as pd
import numpy as np

# Import centralized DB connection
from core.database import get_db_connection

# Import project modules
from ML.lstm_model import create_lstm
from utils.preprocessing import scale_data, create_sequences


# ===================================================
# 3. Model Directory Setup
# ===================================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(SCRIPT_DIR, "models")
os.makedirs(MODEL_DIR, exist_ok=True)


# ===================================================
# 4. Train LSTM for Single Symbol
# ===================================================
def train_for_symbol(symbol, df):

    df = df.sort_values("date")

    data = df["close"].values.reshape(-1, 1)
    scaled, scaler = scale_data(data)

    X, y = create_sequences(scaled)
    X = np.array(X).reshape(X.shape[0], X.shape[1], 1)

    model = create_lstm((X.shape[1], 1))

    model.fit(X, y, epochs=10, batch_size=32, verbose=1)

    model.save(f"{MODEL_DIR}/{symbol}_model.h5")

    print(f"✔ Model saved for {symbol}")


# ===================================================
# 5. Main Training Function
# ===================================================
def main():

    conn = get_db_connection()   # using centralized DB connection
    cur = conn.cursor()

    # Get unique stock symbols
    cur.execute("SELECT DISTINCT symbol FROM stocks")
    symbols = [row[0] for row in cur.fetchall()]

    for symbol in symbols:

        print(f"Training model for: {symbol}")

        df = pd.read_sql(
            "SELECT date, close FROM stocks WHERE symbol=%s ORDER BY date ASC",
            conn,
            params=(symbol,)
        )

        if len(df) < 100:
            print(f"Skipping {symbol} (not enough data)")
            continue

        train_for_symbol(symbol, df)

    cur.close()
    conn.close()


# ===================================================
# 6. Run Script Directly
# ===================================================
if __name__ == "__main__":
    main()