import streamlit as st
import requests
import pandas as pd
from datetime import date
import os

st.set_page_config(page_title="Market Dashboard", layout="wide")

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Content-Type": "application/json"
}

# =============================
# جلب بيانات السوق من TradingView
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
            "relative_volume_10d_calc",
            "price_earnings_ttm",
            "RSI"
        ],
        "sort": {"sortBy": "change", "sortOrder": "desc"},
        "range": [0, 300]
    }

    try:
        r = requests.post(url, json=payload, headers=HEADERS, timeout=15)
        r.raise_for_status()
    except requests.exceptions.RequestException:
        return pd.DataFrame()

    rows = []
    for d in r.json().get("data", []):
        rows.append({
            "Symbol": d["s"],
            "Company": d["d"][1],
            "Price": d["d"][2],
            "Change %": d["d"][3],
            "Relative Volume": d["d"][4],
            "PE": d["d"][5],
            "RSI": d["d"][6]
        })

    return pd.DataFrame(rows)


# =============================
# التحليل والإشارات
# =============================
def add_signals(df):
    if df.empty:
        return df

    df["الحالة"] = "🟡 مراقبة"
    df["إشارة"] = "❌ لا"
    df["نوع الصفقة"] = "-"
    df["سعر الدخول"] = None
    df["جني الأرباح"] = None
    df["وقف الخسارة"] = None
    df["قوة السهم"] = "🔴 ضعيف"
    df["R/R"] = None
    df["تقييم الصفقة"] = None

    # شروط مضاربة قوية
    strong = (
        (df["Change %"] > 2) &
        (df["Relative Volume"] > 1.5) &
        (df["RSI"].between(60, 75))
    )

    # شروط سوينق
    swing = (
        (df["RSI"].between(50, 59)) &
        (df["Relative Volume"] > 1.2)
    )

    # تصنيف
    df.loc[strong, "الحالة"] = "🔥 قوي للشراء"
    df.loc[strong, "إشارة"] = "🔥 شراء"
    df.loc[strong, "نوع الصفقة"] = "مضاربة"
    df.loc[strong, "قوة السهم"] = "⭐⭐⭐ قوي جداً"

    df.loc[swing & ~strong, "الحالة"] = "🟢 مناسب سوينق"
    df.loc[swing & ~strong, "إشارة"] = "🟢 شراء"
    df.loc[swing & ~strong, "نوع الصفقة"] = "سوينق"
    df.loc[swing & ~strong, "قوة السهم"] = "⭐⭐ متوسط"

    # أسعار التداول
    df.loc[strong, "سعر الدخول"] = (df["Price"] * 0.995).round(2)
    df.loc[strong, "جني الأرباح"] = (df["Price"] * 1.06).round(2)
    df.loc[strong, "وقف الخسارة"] = (df["Price"] * 0.97).round(2)

    df.loc[swing & ~strong, "سعر الدخول"] = (df["Price"] * 0.99).round(2)
    df.loc[swing & ~strong, "جني الأرباح"] = (df["Price"] * 1.10).round(2)
    df.loc[swing & ~strong, "وقف الخسارة"] = (df["Price"] * 0.95).round(2)

    # حساب R/R
    rr = (
        (df["جني الأرباح"] - df["سعر الدخول"]) /
        (df["سعر الدخول"] - df["وقف الخسارة"])
    ).round(2)

    df["R/R"] = rr

    df.loc[rr >= 2, "تقييم الصفقة"] = "🔥 ممتاز"
    df.loc[(rr >= 1.5) & (rr < 2), "تقييم الصفقة"] = "🟢 جيد"
    df.loc[rr < 1.5, "تقييم الصفقة"] = "❌ مخاطرة عالية"

    return df


# =============================
# الواجهة
# =============================
st.title("📊 Dashboard الفرص الذكية")

market_choice = st.selectbox("اختر السوق", ["السعودي", "الأمريكي"])

with st.spinner("جاري تحليل السوق..."):
    df = fetch_market("ksa" if market_choice == "السعودي" else "america")
    df = add_signals(df)

if df.empty:
    st.error("❌ لا توجد بيانات")
    st.stop()

# =============================
# أقوى الفرص
# =============================
strong_df = df[df["الحالة"] == "🔥 قوي للشراء"].sort_values("R/R", ascending=False)

# حفظ يومي
today = date.today().isoformat()
filename = f"daily_opportunities_{today}.csv"

if not strong_df.empty and not os.path.exists(filename):
    strong_df.to_csv(filename, index=False, encoding="utf-8-sig")

# =============================
# Tabs
# =============================
tab_all, tab_strong = st.tabs(["📋 كل الأسهم", "🔥 أقوى الفرص الشرائية"])

with tab_all:
    st.dataframe(df, use_container_width=True, hide_index=True)

with tab_strong:
    st.dataframe(strong_df, use_container_width=True, hide_index=True)
