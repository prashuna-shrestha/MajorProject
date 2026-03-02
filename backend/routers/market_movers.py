from fastapi import APIRouter, HTTPException  # FastAPI tools
from pydantic import BaseModel  # For request/response schemas
from sqlalchemy import text
import pandas as pd

from core.database import engine  # ✅ Use centralized engine

router = APIRouter()  # Create a new router

# --- Response models ---
class StockData(BaseModel):
    """
    Schema for each stock's data
    """
    symbol: str
    company_name: str
    current_price: float
    change_percent: float
    last_7_days: list[float]

class MarketMoversResponse(BaseModel):
    """
    Schema for the API response of market movers
    """
    gainers: list[StockData]
    losers: list[StockData]

# --- Endpoint ---
@router.get("/market-movers", response_model=MarketMoversResponse)
def market_movers():
    """
    Get top 10 gainers and losers in the stock market
    """
    try:
        with engine.connect() as conn:  # ✅ Use centralized engine
            query = text("""
                WITH ranked AS (
                    SELECT
                        s.symbol,
                        COALESCE(si.company_name, s.symbol) AS company_name,
                        s.close,
                        LAG(s.close) OVER (PARTITION BY s.symbol ORDER BY s.date) AS prev_close,
                        ROW_NUMBER() OVER (PARTITION BY s.symbol ORDER BY s.date DESC) AS rn
                    FROM stocks s
                    LEFT JOIN stock_info si ON s.symbol = si.symbol
                    WHERE s.close IS NOT NULL
                ),
                latest AS (
                    SELECT *
                    FROM ranked
                    WHERE rn = 1
                ),
                last_days AS (
                    SELECT
                        s.symbol,
                        ARRAY_AGG(s.close ORDER BY s.date DESC) AS all_closes
                    FROM stocks s
                    GROUP BY s.symbol
                )
                SELECT
                    l.symbol,
                    l.company_name,
                    l.close AS current_price,
                    ROUND(
                        ((l.close - l.prev_close) / NULLIF(l.prev_close, 0)) * 100
                    , 2) AS change_percent,
                    ld.all_closes
                FROM latest l
                LEFT JOIN last_days ld ON l.symbol = ld.symbol
                ORDER BY change_percent DESC;
            """)

            df = pd.read_sql(query, conn)

            if df.empty:
                raise HTTPException(status_code=404, detail="No stock data available")

            # Only keep last 7 days of closing prices
            df["last_7_days"] = df["all_closes"].apply(lambda x: x[:7] if x else [])

            # Top 10 gainers
            gainers_df = df[df["change_percent"] > 0].nlargest(10, "change_percent")
            gainers = gainers_df.to_dict(orient="records")

            # Top 10 losers
            losers_df = df[df["change_percent"] < 0].nsmallest(10, "change_percent")
            losers = losers_df.to_dict(orient="records")

            # Ensure dict keys match Pydantic model
            for g in gainers:
                g["last_7_days"] = g.pop("last_7_days")
            for l in losers:
                l["last_7_days"] = l.pop("last_7_days")

            return {
                "gainers": gainers,
                "losers": losers
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SQL ERROR: {e}")