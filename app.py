import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import os

st.set_page_config(page_title="Market Dashboard", layout="wide")

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Content-Type": "application/json"
}

TRADES_FILE = "trades.csv"  # ملف حفظ الصفقات

# =============================
# جلب بيانات السوق
# =============================
def fetch_market(market):
    url = f"https://scanner.tradingview.com/{market}/scan"
    payload = {
        "filter": [],
        "symbols": {"query": {"types": []}, "tickers": []},
        "columns": [
            "name", "description", "close", "change",
            "relative_volume_10d_calc", "price_earnings_ttm"
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
        try:
            price = float(d["d"][2]) if d["d"][2] is not None else 0
            change = float(d["d"][3]) if d["d"][3] is not None else 0
            rel_vol = float(d["d"][4]) if d["d"][4] is not None else 0
            pe = float(d["d"][5]) if d["d"][5] is not None else None
        except (ValueError, TypeError):
            price = change = rel_vol = 0
            pe = None

        rows.append({
            "Symbol": d["s"],
            "Company": d["d"][1] if d["d"][1] else "",
            "Price": price,
            "Change %": change,
            "Relative Volume": rel_vol,
            "PE": pe
        })

    return pd.DataFrame(rows)

# =============================
# إشارات وحالة السهم
# =============================
def add_signals(df):
    if df.empty:
        return df

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
    df.loc[strong_buy, "سعر الدخول"] = df["Price"]
    df.loc[strong_buy, "جني الأرباح"] = (df["Price"] * 1.05).round(2)
    df.loc[strong_buy, "وقف الخسارة"] = (df["Price"] * 0.975).round(2)

    df.loc[potential_buy & ~strong_buy, "إشارة"] = "⚡ متابعة"
    df.loc[potential_buy & ~strong_buy, "سعر الدخول"] = df["Price"]
    df.loc[potential_buy & ~strong_buy, "جني الأرباح"] = (df["Price"] * 1.03).round(2)
    df.loc[potential_buy & ~strong_buy, "وقف الخسارة"] = (df["Price"] * 0.985).round(2)

    return df

# =============================
# إدارة الصفقة
# =============================
def analyze_trade(symbol, buy_price, current_price):
    change_pct = ((current_price - buy_price) / buy_price) * 100
    recommendation = "استمر بالاحتفاظ" if change_pct < 5 else "فكر في البيع"
    return change_pct, recommendation

# =============================
# تحميل وحفظ الصفقات
# =============================
def load_trades():
    if os.path.exists(TRADES_FILE):
        return pd.read_csv(TRADES_FILE)
    return pd.DataFrame(columns=["Symbol","Buy Price","Quantity","Date"])

def save_trades(df):
    df.to_csv(TRADES_FILE, index=False)

# =============================
# الواجهة مع التابات العلوية
# =============================
st.title("📊 Market Dashboard")

tab1, tab2, tab3, tab4 = st.tabs(["فرص مضاربية", "أقوى الأسهم", "إدارة الصفقة", "تتبع الصفقات"])

# -----------------------------
# تاب 1: فرص مضاربية
# -----------------------------
with tab1:
    st.header("📊 فرص مضاربية")
    market_choice = st.selectbox("اختر السوق", ["السعودي", "الأمريكي"])
    with st.spinner(f"جلب بيانات سوق {market_choice}..."):
        df = fetch_market("ksa") if market_choice == "السعودي" else fetch_market("america")
    df = add_signals(df)
    if df.empty:
        st.error("❌ لم يتم جلب أي بيانات")
    else:
        st.success(f"تم تحميل {len(df)} سهم")
        st.dataframe(df, use_container_width=True, hide_index=True)

# -----------------------------
# تاب 2: أقوى الأسهم
# -----------------------------
with tab2:
    st.header("💪 أقوى الأسهم")
    df_sa = fetch_market("ksa")
    df_usa = fetch_market("america")
    df_all = pd.concat([df_sa, df_usa], ignore_index=True)
    df_all = add_signals(df_all)
    strong_stocks = df_all[df_all["قوة السهم"] == "⭐ قوي"]
    st.dataframe(strong_stocks, use_container_width=True, hide_index=True)
    if strong_stocks.empty:
        st.info("لا توجد فرص قوية حالياً.")

# -----------------------------
# تاب 3: إدارة الصفقة
# -----------------------------
with tab3:
    st.header("📝 إدارة الصفقة")
    symbol_input = st.text_input("رمز السهم")
    buy_price_input = st.number_input("سعر الشراء", min_value=0.0, format="%.2f")
    current_price_input = st.number_input("السعر الحالي", min_value=0.0, format="%.2f")
    if st.button("تحليل الصفقة"):
        if symbol_input and buy_price_input > 0 and current_price_input > 0:
            change_pct, rec = analyze_trade(symbol_input, buy_price_input, current_price_input)
            st.write(f"🔹 التغير منذ الشراء: {change_pct:.2f}%")
            st.write(f"🔹 التوصية: {rec}")
        else:
            st.warning("يرجى إدخال جميع القيم.")

# -----------------------------
# تاب 4: تتبع الصفقات
# -----------------------------
with tab4:
    st.header("📈 تتبع الصفقات")
    trades_df = load_trades()

    with st.form("add_trade_form"):
        symbol = st.text_input("رمز السهم")
        buy_price = st.number_input("سعر الشراء", min_value=0.0, format="%.2f")
        quantity = st.number_input("عدد الأسهم", min_value=1, step=1)
        date = st.date_input("تاريخ الشراء", value=datetime.today())
        submitted = st.form_submit_button("إضافة الصفقة")
        if submitted and symbol and buy_price > 0:
            trades_df = trades_df.append({
                "Symbol": symbol,
                "Buy Price": buy_price,
                "Quantity": quantity,
                "Date": date
            }, ignore_index=True)
            save_trades(trades_df)
            st.success(f"تم إضافة الصفقة: {symbol}")

    if not trades_df.empty:
        st.subheader("📋 صفقاتك الحالية")
        st.dataframe(trades_df, use_container_width=True, hide_index=True)
