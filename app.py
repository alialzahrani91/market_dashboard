import streamlit as st
import requests
import pandas as pd
import os
from datetime import datetime

st.set_page_config(page_title="Market Dashboard", layout="wide")

HEADERS = {"User-Agent": "Mozilla/5.0","Content-Type": "application/json"}
TRADES_FILE = "trades.csv"

# =============================
# جلب بيانات السوق
# =============================
def fetch_market(market):
    url = f"https://scanner.tradingview.com/{market}/scan"
    payload = {
        "filter": [],
        "symbols": {"query": {"types": []}, "tickers": []},
        "columns": [
            "name","description","close","change",
            "relative_volume_10d_calc","price_earnings_ttm"
        ],
        "sort": {"sortBy": "change", "sortOrder": "desc"},
        "range": [0, 300]
    }
    try:
        r = requests.post(url, json=payload, headers=HEADERS, timeout=15)
        r.raise_for_status()
    except:
        return pd.DataFrame()
    data = r.json().get("data", [])
    rows = []
    for d in data:
        try:
            rows.append({
                "Symbol": d["s"],
                "Company": d["d"][1],
                "Price": float(d["d"][2]),
                "Change %": float(d["d"][3]),
                "Relative Volume": float(d["d"][4]),
                "PE": float(d["d"][5])
            })
        except:
            continue
    return pd.DataFrame(rows)

# =============================
# إضافة إشارات وحالة السهم
# =============================
def add_signals(df):
    if df.empty: return df
    df["الحالة"] = "🟡 مراقبة"
    df["إشارة"] = "❌ لا"
    df["سعر الدخول"] = None
    df["جني الأرباح"] = None
    df["وقف الخسارة"] = None
    df["قوة السهم"] = "🔴 ضعيف"

    strong_buy = (df["Change %"] > 2) & (df["Relative Volume"] > 1.5) & (df["PE"] < 30)
    potential_buy = ((df["Change %"] > 1) | (df["Relative Volume"] > 1.2)) & (df["PE"] < 50)

    df.loc[strong_buy, "الحالة"] = "⭐ قوي للشراء"
    df.loc[potential_buy & ~strong_buy, "الحالة"] = "⚡ فرصة محتملة"
    df.loc[df["Change %"] < 0, "الحالة"] = "🔴 ضعيف"

    df.loc[strong_buy, "قوة السهم"] = "⭐ قوي"
    df.loc[potential_buy & ~strong_buy, "قوة السهم"] = "⚡ متوسط"

    df.loc[strong_buy, "إشارة"] = "🔥 شراء"
    df.loc[strong_buy, "سعر الد_]()
