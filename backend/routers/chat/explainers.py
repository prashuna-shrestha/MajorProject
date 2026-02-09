def explain_rsi_simple(rsi: float) -> str:
    if rsi >= 70:
        return f"📈 RSI {rsi:.1f}: The stock may be OVERBOUGHT (price went up too fast)."
    if rsi <= 30:
        return f"📉 RSI {rsi:.1f}: The stock may be OVERSOLD (price dropped too fast)."
    return f"⚖️ RSI {rsi:.1f}: The stock is in a NORMAL range."


def explain_ema_simple(ema12: float, ema26: float) -> str:
    if ema12 > ema26:
        return (
            f"🟢 Short-term trend is ABOVE long-term trend → "
            f"price momentum looks POSITIVE."
        )
    if ema12 < ema26:
        return (
            f"🔴 Short-term trend is BELOW long-term trend → "
            f"price momentum looks WEAK."
        )
    return "🟡 Short-term and long-term trends are CLOSE → no clear direction."


def explain_bb_simple(price: float, upper: float, lower: float) -> str:
    if price > upper:
        return (
            "🚀 Price is VERY HIGH compared to normal → "
            "strong move, but may be overstretched."
        )
    if price < lower:
        return (
            "🧊 Price is VERY LOW compared to normal → "
            "weak move, but may rebound."
        )
    return "🌊 Price is moving normally → no unusual volatility."