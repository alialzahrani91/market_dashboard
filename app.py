import streamlit as st
import requests
import pandas as pd
from bs4 import BeautifulSoup

st.set_page_config(page_title="Market Dashboard", layout="wide")

# =============================
# جلب البيانات من TradingView
# =============================
def fetch_tradingview_stocks(url, market_suffix):
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers, timeout=15)
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")
    rows = soup.select("tr.row-RdUXZpkv")

    data = []

    for row in rows:
        try:
            symbol_tag = row.select_one("a.tickerNameBox-GrtoTeat")
            name_tag   = row.select_one("a.tickerDescription-GrtoTeat")

            price_tag  = row.select_one("td[data-field='Price']")
            change_tag = row.select_one("td[data-field='Change|TimeResolution1D']")
            volume_tag = row.select_one("td[data-field='RelativeVolume|TimeResolution1D']")

            if not symbol_tag or not price_tag:
                continue

            symbol = symbol_tag.text.strip()
            name = name_tag.text.strip() if name_tag else ""

            price = float(price_tag.text.replace(",", ""))
            change = float(change_tag.text.replace("%", "")) if change_tag else 0
            rel_volume = float(volume_tag.text) if volume_tag else 0

            data.append({
                "Symbol": f"{symbol}.{market_suffix}",
                "Company": name,
                "Price": price,
                "Change %": change,
                "Relative Volume": rel_volume
            })

        except Exception:
            continue

    return pd.DataFrame(data)


# =============================
# حساب إشارات التداول
# =============================
def add_trading_signals(df):
    signals = []

    for _, row in df.iterrows():
        price = row["Price"]
        change = row["Change %"]
        rv = row["Relative Volume"]

        if change > 2 and rv > 1.5:
            signals.append({
                "Opportunity": "✅ نعم",
                "Entry Price": round(price, 2),
                "Take Profit": round(price * 1.05, 2),
                "Stop Loss": round(price * 0.975, 2),
                "Strength": "⭐ قوي"
            })
        elif change > 0:
            signals.append({
                "Opportunity": "⚠️ مراقبة",
                "Entry Price": None,
                "Take Profit": None,
                "Stop Loss": None,
                "Strength": "🟡 متوسط"
            })
        else:
            signals.append({
                "Opportunity": "❌ لا",
                "Entry Price": None,
                "Take Profit": None,
                "Stop Loss": None,
                "Strength": "🔴 ضعيف"
            })

    return pd.concat
