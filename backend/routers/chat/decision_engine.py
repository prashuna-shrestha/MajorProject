
def decision_from_prediction(pred: dict) -> str:
    """
    Decide BUY/HOLD/SELL mainly from LSTM derived prediction trends.

    Uses:
    - trends: very_short_term, short_term, mid_term, long_term
      (values expected: "Uptrend", "Downtrend", "Sideways")
    - confidence: value between 0-100 representing model certainty
    """

    # Extract confidence score from prediction dictionary
    # If confidence key does not exist, default value = 0
    conf = float(pred.get("confidence", 0))

    # ---------------------------------------------------
    # If confidence is too low, avoid strong decision
    # This prevents acting on weak model predictions
    # ---------------------------------------------------
    if conf < 55:
        return "HOLD"

    # ---------------------------------------------------
    # Collect trend predictions for different timeframes
    # ---------------------------------------------------
    trends = [
        pred.get("very_short_term"),  
        pred.get("short_term"),       
        pred.get("mid_term"),       
        pred.get("long_term"),        
    ]

    # Count how many trends are Uptrend
    up = sum(1 for t in trends if t == "Uptrend")

    # Count how many trends are Downtrend
    down = sum(1 for t in trends if t == "Downtrend")

    # Count how many trends are Sideways
    side = sum(1 for t in trends if t == "Sideways")

    # ---------------------------------------------------
    # STRONG BIAS LOGIC
    # ---------------------------------------------------

    # If at least 3 trends are Uptrend and none are Downtrend
    # Strong bullish signal
    if up >= 3 and down == 0:
        return "BUY"

    # If at least 3 trends are Downtrend and none are Uptrend
    # Strong bearish signal
    if down >= 3 and up == 0:
        return "SELL"

    # ---------------------------------------------------
    # MIXED SIGNALS
    # ---------------------------------------------------

    # If 2 or more timeframes are sideways
    # Market is unclear → HOLD
    if side >= 2:
        return "HOLD"

    # ---------------------------------------------------
    # SLIGHT BIAS LOGIC
    # ---------------------------------------------------

    # If more uptrends than downtrends → slight bullish
    if up > down:
        return "BUY"

    # If more downtrends than uptrends → slight bearish
    if down > up:
        return "SELL"

    # If equal or unclear → HOLD
    return "HOLD"


def trade_decision(ctx, horizon="1M"):
    """
    Final decision uses LSTM-derived prediction as PRIMARY signal,
    and uses EMA / RSI / technical status as SECONDARY confirmation.

    ctx = stock context dictionary
    horizon = investment timeframe 
    """

    # ---------------------------------------------------
    # STEP 1: Get primary decision from prediction engine
    # ---------------------------------------------------
    pred_decision = decision_from_prediction(ctx["prediction"])

    # ---------------------------------------------------
    # STEP 2: Calculate confirmation score
    # (technical indicators support or reject prediction)
    # ---------------------------------------------------
    confirm = 0

    # If short EMA (12) > long EMA (26)
    # This is typically bullish crossover
    if ctx["ema12"] > ctx["ema26"]:
        confirm += 1

    # If RSI between 40 and 70
    # Not overbought (>70) and not oversold (<30)
    # Indicates healthy trend
    if 40 < ctx["rsi"] < 70:
        confirm += 1

    # If short-term technical status says Uptrend
    if ctx["technical"].get("short_term") == "Uptrend":
        confirm += 1

    # ---------------------------------------------------
    # STEP 3: Risk Adjustment Logic
    # ---------------------------------------------------

    # If model says BUY but confirmation score is 0
    # That means indicators disagree → downgrade to HOLD
    if pred_decision == "BUY" and confirm == 0:
        return "HOLD"

    # If model says SELL but confirmation looks bullish (>=2)
    # Avoid strong sell → downgrade to HOLD
    if pred_decision == "SELL" and confirm >= 2:
        return "HOLD"

    # Otherwise, follow model decision
    return pred_decision