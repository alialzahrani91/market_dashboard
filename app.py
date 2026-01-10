import streamlit as st
import pandas as pd
import yfinance as yf

st.set_page_config(layout="wide")
st.title("📊 داشبورد فرص المضاربة")

# -----------------------------
# RSI
# -----------------------------
def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

# -----------------------------
# Signal
# -----------------------------
def technical_signal(price, sma, rsi):
    if price > sma and rsi < 70:
        return "Buy"
    elif price < sma and rsi > 30:
        return "Sell"
    else:
        return "Neutral"

# -----------------------------
# تصنيف الفرصة
# -----------------------------
def opportunity(signal):
    if signal == "Buy":
        return "فرصة مضاربية"
    elif signal == "Neutral":
        return "انتظار"
    else:
        return "عدم دخول"

# -----------------------------
# رموز تجريبية (لاحقًا نربطها تلقائيًا)
# -----------------------------
symbols = [
    "1010.SR", "2222.SR", "2010.SR",
    "AAPL", "MSFT", "NVDA"
]

rows = []

for symbol in symbols:
    try:
        stock = yf.Ticker(symbol)
        hist = stock.history(period="1mo")

        if hist.empty:
            continue

        close = hist["Close"]
        price = round(close.iloc[-1], 2)
        sma20 = round(close.rolling(20).mean().iloc[-1], 2)
        rsi14 = round(calculate_rsi(close).iloc[-1], 2)

        signal = technical_signal(price, sma20, rsi14)
        opp = opportunity(signal)

        entry = round(price * 0.99, 2) if signal == "Buy" else None
        target = round(price * 1.05, 2) if signal == "Buy" else None

        rows.append({
            "الرمز": symbol,
            "السعر": price,
            "SMA20": sma20,
            "RSI": rsi14,
            "الإشارة": signal,
            "التصنيف": opp,
            "سعر الدخول": entry,
            "سعر جني الربح": target,
            "تنبيه": "🔥 شراء الآن" if signal == "Buy" else ""
        })

    except Exception:
        continue

df = pd.DataFrame(rows)

# -----------------------------
# فلاتر الواجهة
# -----------------------------
col1, col2 = st.columns(2)

with col1:
    refre
