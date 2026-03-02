# ===================================================
# 1. Package Imports
# ===================================================
from pathlib import Path
import pandas as pd
from psycopg2.extras import execute_values

# Import centralized DB connection
from core.database import get_db_connection


# ===================================================
# 2. Stock Info Pipeline Function
# ===================================================
def run_stock_info_pipeline(
    merged_stock_path=None,
    company_list_path=None,
    output_path=None
):
    """
    Stock Info Pipeline:
    1. Load merged stock CSV and company list CSV
    2. Clean and merge data
    3. Save cleaned CSV
    4. Insert or update data into PostgreSQL
    """

    base_path = Path(__file__).parent

    # ------------------------------------------------
    # Default File Paths
    # ------------------------------------------------
    if merged_stock_path is None:
        merged_stock_path = base_path / "../../data/clean/merged_stock_nepse.csv"

    if company_list_path is None:
        company_list_path = base_path / "../../data/raw/CompanyList.csv"

    if output_path is None:
        output_path = base_path / "../../data/clean/clean_stock_info.csv"

    # ------------------------------------------------
    # Load CSV Files
    # ------------------------------------------------
    merged_df = pd.read_csv(merged_stock_path)
    company_df = pd.read_csv(company_list_path)

    # ------------------------------------------------
    # Prepare Company Info
    # ------------------------------------------------
    company_df = company_df[['Symbol', 'Company Name', 'Sector']].copy()
    company_df.columns = ['symbol', 'company_name', 'category']

    # ------------------------------------------------
    # Standardize Symbols
    # ------------------------------------------------
    merged_df['symbol'] = (
        merged_df['symbol']
        .astype(str)
        .str.strip()
        .str.upper()
    )

    company_df['symbol'] = (
        company_df['symbol']
        .astype(str)
        .str.strip()
        .str.upper()
    )

    # ------------------------------------------------
    # Merge Data
    # ------------------------------------------------
    merged_info = pd.merge(
        merged_df[['symbol']].drop_duplicates(),
        company_df,
        on='symbol',
        how='left'
    )

    # ------------------------------------------------
    # Handle Missing Values
    # ------------------------------------------------
    merged_info['company_name'] = merged_info['company_name'].fillna('Unknown Company')
    merged_info['category'] = merged_info['category'].fillna('Others')

    merged_info = merged_info.drop_duplicates(subset=['symbol'])

    # ------------------------------------------------
    # Save Cleaned CSV
    # ------------------------------------------------
    output_path.parent.mkdir(parents=True, exist_ok=True)
    merged_info.to_csv(output_path, index=False)

    print(f"Cleaned stock info saved to: {output_path}")

    # ------------------------------------------------
    # Insert / Update into PostgreSQL
    # ------------------------------------------------
    conn = get_db_connection()
    cur = conn.cursor()

    values = [tuple(row) for row in merged_info.to_numpy()]
    batch_size = 100

    for i in range(0, len(values), batch_size):
        execute_values(
            cur,
            """
            INSERT INTO stock_info (symbol, company_name, category)
            VALUES %s
            ON CONFLICT (symbol)
            DO UPDATE SET
                company_name = EXCLUDED.company_name,
                category = EXCLUDED.category
            """,
            values[i:i + batch_size]
        )

    conn.commit()
    cur.close()
    conn.close()

    print(f"{len(values)} rows inserted/updated in stock_info table.")

    return merged_info


# ===================================================
# 3. Run Pipeline Directly
# ===================================================
if __name__ == "__main__":
    run_stock_info_pipeline()