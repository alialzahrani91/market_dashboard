import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Market Dashboard", layout="wide")

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Content-Type": "application/json"
}

# =============================
# جلب بيانات السوق
# =============================
def fetch_market(market):
    url = f"https://scanner.tradingview.com/{market}/scan"
    payload = {
        "filter": [],
        "symbols": {"query": {"types": []}, "tickers": []},
        "columns": [
            "name",                   # اسم الشركة
            "description",            # الرمز
            "close",                  # السعر
            "change",                 # تغير %
            "relative_volume_10d_calc", # حجم نسبي
            "price_earnings_ttm",     # PE
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
            "Price": float(d["d"][2]),
            "Change %": float(d["d"][3]),
            "Relative Volume": float(d["d"][4]),
            "PE": float(d["d"][5]) if d["d"][5] is not None else None
        })

    return pd.DataFrame(rows)


# =============================
# إضافة إشارات وحالة السهم
# =============================
def add_signals(df):
    if df.empty:
        return df

    # أعمدة افتراضية
    df["الحالة"] = "🟡 مراقبة"
    df["إشارة"] = "❌ لا"
    df["سعر الدخول"] = None
    df["جني الأرباح"] = None
    df["وقف الخسارة"] = None
    df["قوة السهم"] = "🔴 ضعيف"

    # شروط الشراء
    strong_buy = (df["Change %"] > 2) & (df["Relative Volume"] > 1.5) & ((df["PE"].fillna(100)) < 30)
    potential_buy = ((df["Change %"] > 1) | (df["Relative Volume"] > 1.2)) & ((df["PE"].fillna(100)) < 50)

    # تصنيف الحالة
    df.loc[strong_buy, "الحالة"] = "⭐ قوي للشراء"
    df.loc[potential_buy & ~strong_buy, "الحالة"] = "⚡ فرصة محتملة"
    df.loc[df["Change %"] < 0, "الحالة"] = "🔴 ضعيف"

    # قوة السهم
    df.loc[strong_buy, "قوة السهم"] = "⭐ قوي"
    df.loc[potential_buy & ~strong_buy, "قوة السهم"] = "⚡ متوسط"

    # إشارات الدخول والجني ووقف الخسارة
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
# جلب بيانات سهم واحد
# =============================
def fetch_single_symbol(symbol):
    url = "https://scanner.tradingview.com/global/scan"
    payload = {
        "symbols": {"tickers": [symbol], "query": {"types": []}},
        "columns": ["close", "change", "RSI", "relative_volume_10d_calc"]
    }
    r = requests.post(url, json=payload, headers=HEADERS, timeout=15)
    if r.status_code != 200:
        return None
    data = r.json().get("data", [])
    if not data:
        return None
    d = data[0]["d"]
    return {
        "Price": float(d[0]),
        "Change %": float(d[1]),
        "RSI": float(d[2]) if d[2] is not None else None,
        "RelVol": float(d[3]) if d[3] is not None else None
    }


# =============================
# واجهة المستخدم
# =============================
st.title("📊 Dashboard الفرص المضاربية")

tab1, tab2, tab3 = st.tabs(["📊 السوق", "💪 أقوى الأسهم", "🧠 إدارة الصفقة"])

# -----------------------------
# تاب السوق
# -----------------------------
with tab1:
    market_choice = st.selectbox("اختر السوق", ["السعودي", "الأمريكي"])
    with st.spinner(f"جلب بيانات سوق {market_choice}..."):
        if market_choice == "السعودي":
            df = fetch_market("ksa")
        else:
            df = fetch_market("america")

    df = add_signals(df)

    if df.empty:
        st.error("❌ لم يتم جلب أي بيانات من TradingView")
        st.stop()

    st.success(f"تم تحميل {len(df)} سهم")
    st.dataframe(df, use_container_width=True, hide_index=True)

# -----------------------------
# تاب أقوى الأسهم
# -----------------------------
with tab2:
    st.subheader("💪 أقوى الأسهم للشراء حالياً")
    if df.empty:
        st.warning("⚠️ البيانات غير متوفرة")
    else:
        strong_df = df[df["الحالة"] == "⭐ قوي للشراء"]
        if strong_df.empty:
            st.info("لا توجد فرص قوية حالياً")
        else:
            st.dataframe(strong_df, use_container_width=True, hide_index=True)

# -----------------------------
# تاب إدارة الصفقة
# -----------------------------
with tab3:
    st.subheader("🧠 إدارة الصفقة الذكية")
    col1, col2 = st.columns(2)

    with col1:
        symbol = st.text_input("رمز السهم (مثال: TADAWUL:1010 أو NASDAQ:AAPL)")
    with col2:
        buy_price = st.number_input("سعر الشراء", min_value=0.0, step=0.01)

    if st.button("🔍 تحليل الصفقة") and symbol and buy_price > 0:
        data = fetch_single_symbol(symbol)
        if not data:
            st.error("❌ لم يتم جلب بيانات السهم")
        else:
            current = data["Price"]
            rsi = data["RSI"]
            pnl_pct = ((current - buy_price) / buy_price) * 100

            st.markdown("### 📈 نتائج التحليل")
            c1, c2, c3 = st.columns(3)
            c1.metric("السعر الحالي", round(current, 2))
            c2.metric("الربح / الخسارة %", f"{pnl_pct:.2f}%")
            c3.metric("RSI", round(rsi, 1) if rsi else "N/A")
            st.markdown("---")

            # ===== قرار ذكي =====
            decision = "👀 مراقبة"
            color = "🟡"

            if pnl_pct <= -5:
                decision = "⛔ وقف خسارة – يفضل الخروج"
                color = "🔴"
            elif rsi and rsi > 75 and pnl_pct > 0:
                decision = "🔴 بيع / جني أرباح"
                color = "🔴"
            elif rsi and 65 <= rsi <= 75:
                decision = "🟡 جني أرباح جزئي"
                color = "🟡"
            elif rsi and rsi < 65 and pnl_pct >= 0:
                decision = "🟢 استمرار – الترند إيجابي"
                color = "🟢"

            st.markdown(f"## {color} القرار: **{decision}**")
