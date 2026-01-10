import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Market Dashboard", layout="wide")

# =============================
# TradingView Scanner API
# =============================
def fetch_market(market):
    url = f"https://scanner.tradingview.com/{market}/scan"

    payload = {
        "filter": [],
        "symbols": {"query": {"types": []}, "tickers": []},
        "columns": [
            "name",
            "description",
            "close",
            "change",
            "relative_volume_10d_calc"
        ],
        "sort": {"sortBy": "change", "sortOrder": "desc"},
        "range": [0, 300]
    }

    r = requests.post(url, json=payload, timeout=15)
    r.raise_for_status()

    data = r.json()["data"]

    rows = []
    for d in data:
        rows.append({
            "Symbol": d["s"],
            "Company": d["d"][1],
            "Price": d["d"][2],
            "Change %": d["d"][3],
            "Relative Volume": d["d"][4]
        })

    return pd.DataFrame(rows)


# =============================
# إشارات التداول
# =============================
def add_signals(df):
    signals = []

    for _, r in df.iterrows():
        price = r["Price"]
        ch = r["Change %"]
        rv = r["Relative Volume"]

        if ch > 2 and rv > 1.5:
            signals.append(("🔥 شراء", price, price * 1.05, price * 0.975, "⭐ قوي"))
        elif ch > 0:
            signals.append(("⚠️ مراقبة", None, None, None, "🟡 متوسط"))
        else:
            signals.append(("❌ لا", None, None, None, "🔴 ضعيف"))

    df["إشارة"] = [s[0] for s in signals]
    df["سعر الدخول"] = [round(s[1], 2) if s[1] else None for s in signals]
    df["جني الأرباح"] = [round(s[2], 2) if s[2] else None for s in signals]
    df["وقف الخسارة"] = [round(s[3], 2) if s[3] else None for s in signals]
    df["قوة السهم"] = [s[4] for s in signals]

    return df


# =============================
# الواجهة
# =============================
st.title("📊 Dashboard الفرص المضاربية")

with st.spinner("جلب السوق السعودي والأمريكي..."):
    saudi = fetch_market("saudi")
    usa = fetch_market("america")

df = pd.concat([saudi, usa], ignore_index=True)
df = add_signals(df)

st.success(f"تم تحميل {len(df)} سهم")

st.dataframe(df, use_container_width=True, hide_index=True)
