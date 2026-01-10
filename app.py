import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Market Dashboard", layout="wide")

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Content-Type": "application/json"
}

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

    r = requests.post(url, json=payload, headers=HEADERS, timeout=15)

    if r.status_code != 200:
        st.warning(f"⚠️ تعذر جلب سوق {market}")
        return pd.DataFrame()

    data = r.json().get("data", [])

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
    if df.empty:
        return df

    df["إشارة"] = "❌ لا"
    df["سعر الدخول"] = None
    df["جني الأرباح"] = None
    df["وقف الخسارة"] = None
    df["قوة السهم"] = "🔴 ضعيف"

    buy = (df["Change %"] > 2) & (df["Relative Volume"] > 1.5)

    df.loc[buy, "إشارة"] = "🔥 شراء"
    df.loc[buy, "سعر الدخول"] = df["Price"]
    df.loc[buy, "جني الأرباح"] = (df["Price"] * 1.05).round(2)
    df.loc[buy, "وقف الخسارة"] = (df["Price"] * 0.975).round(2)
    df.loc[buy, "قوة السهم"] = "⭐ قوي"

    return df


# =============================
# الواجهة
# =============================
st.title("📊 Dashboard الفرص المضاربية")

with st.spinner("جلب السوق السعودي والأمريكي..."):
    saudi = fetch_market("ksa")
    usa = fetch_market("america")

df = pd.concat([saudi, usa], ignore_index=True)
df = add_signals(df)

if df.empty:
    st.error("❌ لم يتم جلب أي بيانات من TradingView")
    st.stop()

st.success(f"تم تحميل {len(df)} سهم")
st.dataframe(df, use_container_width=True, hide_index=True)
