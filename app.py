import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Market Dashboard", layout="wide")

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Content-Type": "application/json"
}

# =============================
# أدوات مساعدة
# =============================
def to_numeric_safe(df, cols):
    for c in cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


# =============================
# جلب بيانات السوق من TradingView
# =============================
def fetch_market(market):
    url = f"https://scanner.tradingview.com/{market}/scan"

    payload = {
        "filter": [],
        "symbols": {"query": {"types": []}, "tickers": []},
        "columns": [
            "name",                    # الرمز
            "description",             # اسم الشركة
            "close",                   # السعر
            "change",                  # التغير %
            "relative_volume_10d_calc",# الحجم النسبي
            "price_earnings_ttm",      # PE
            "RSI"                      # RSI
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
            "Relative Volume": d["d"][4],
            "PE": d["d"][5],
            "RSI": d["d"][6]
        })

    return pd.DataFrame(rows)


# =============================
# إضافة التحليل والإشارات
# =============================
def add_signals(df):
    if df.empty:
        return df

    df = to_numeric_safe(
        df,
        ["Price", "Change %", "Relative Volume", "PE", "RSI"]
    )

    # أعمدة افتراضية
    df["نوع الصفقة"] = "—"
    df["الحالة"] = "🟡 مراقبة"
    df["إشارة"] = "❌ لا"
    df["قوة السهم"] = "🔴 ضعيف"
    df["سعر الدخول"] = None
    df["جني الأرباح"] = None
    df["وقف الخسارة"] = None
    df["R/R"] = None

    # ===== شروط =====
    scalp = (
        (df["RSI"] > 30) & (df["RSI"] < 55) &
        (df["Change %"] > 1.5) &
        (df["Relative Volume"] > 1.5)
    )

    swing = (
        (df["RSI"] >= 55) & (df["RSI"] <= 70) &
        (df["Change %"] > 0) &
        (df["PE"] < 40)
    )

    # ===== مضاربة =====
    df.loc[scalp, "نوع الصفقة"] = "⚡ مضاربة"
    df.loc[scalp, "الحالة"] = "🔥 فرصة قوية"
    df.loc[scalp, "إشارة"] = "شراء"
    df.loc[scalp, "قوة السهم"] = "⭐⭐⭐"

    df.loc[scalp, "سعر الدخول"] = df["Price"] * 0.995
    df.loc[scalp, "جني الأرباح"] = df["Price"] * 1.04
    df.loc[scalp, "وقف الخسارة"] = df["Price"] * 0.97

    # ===== سوينق =====
    df.loc[swing & ~scalp, "نوع الصفقة"] = "📈 سوينق"
    df.loc[swing & ~scalp, "الحالة"] = "⭐ جيدة"
    df.loc[swing & ~scalp, "إشارة"] = "شراء"
    df.loc[swing & ~scalp, "قوة السهم"] = "⭐⭐"

    df.loc[swing & ~scalp, "سعر الدخول"] = df["Price"] * 0.99
    df.loc[swing & ~scalp, "جني الأرباح"] = df["Price"] * 1.08
    df.loc[swing & ~scalp, "وقف الخسارة"] = df["Price"] * 0.94

    # ===== حساب R/R =====
    df["R/R"] = (
        (df["جني الأرباح"] - df["سعر الدخول"]) /
        (df["سعر الدخول"] - df["وقف الخسارة"])
    )

    df["R/R"] = pd.to_numeric(df["R/R"], errors="coerce").round(2)

    return df


# =============================
# واجهة المستخدم
# =============================
st.title("📊 Dashboard الفرص الذكية")

market_choice = st.selectbox(
    "اختر السوق",
    ["السعودي", "الأمريكي"]
)

with st.spinner("جلب البيانات..."):
    if market_choice == "السعودي":
        df = fetch_market("ksa")
    else:
        df = fetch_market("america")

df = add_signals(df)

if df.empty:
    st.error("❌ لم يتم جلب بيانات")
    st.stop()

# =============================
# Tabs
# =============================
tab1, tab2 = st.tabs(["📋 جميع الأسهم", "🔥 أقوى الفرص"])

with tab1:
    st.success(f"تم تحميل {len(df)} سهم")
    st.dataframe(df, use_container_width=True, hide_index=True)

with tab2:
    strong = df[
        (df["إشارة"] == "شراء") &
        (df["R/R"] >= 2) &
        (df["RSI"] < 70)
    ].sort_values("R/R", ascending=False)

    if strong.empty:
        st.info("لا توجد فرص قوية حالياً")
    else:
        st.success(f"🔥 {len(strong)} فرصة قوية")
        st.dataframe(strong, use_container_width=True, hide_index=True)
