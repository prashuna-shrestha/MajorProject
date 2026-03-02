# ===================================================
# 1. Package Imports
# ===================================================
import pandas as pd
from psycopg2.extras import execute_values
from core.database import get_db_connection


# ===================================================
# 2. CSV File Path
# ===================================================
csv_file = '../../data/clean/merged_stock_nepse.csv'


# ===================================================
# 3. Load and Prepare Data
# ===================================================
df = pd.read_csv(csv_file, parse_dates=['date'])

# Convert pandas Timestamp to Python date
df['date'] = df['date'].dt.date

# Columns that should be numeric
numeric_cols = ['open', 'high', 'low', 'close', 'close_norm']

# Convert NaN → None and ensure float type
for col in numeric_cols:
    df[col] = df[col].apply(
        lambda x: float(x) if pd.notnull(x) else None
    )

# Convert DataFrame to list of tuples
values = [tuple(row) for row in df.itertuples(index=False, name=None)]


# ===================================================
# 4. Insert Data into PostgreSQL
# ===================================================
conn = get_db_connection()   #  Using centralized DB connection
cur = conn.cursor()

execute_values(
    cur,
    """
    INSERT INTO stocks (date, symbol, open, high, low, close, close_norm)
    VALUES %s
    """,
    values
)

conn.commit()
cur.close()
conn.close()

print("CSV imported successfully!")