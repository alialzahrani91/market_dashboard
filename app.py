import streamlit as st
import requests
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Market Dashboard", layout="wide")

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Content-Type": "application/json"
}

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
            "name",
            "description",
            "close",
            "change",
            "relative_volume_10d_calc",
            "price_earnings_ttm",
        ],
        "sort": {"sortBy": "change", "sortOrder": "desc"},
        "range": [0, 300]
    }

    try:
        r = requests.post(url, json=payload, headers=HEADERS, timeout=15)
        r.raise_for_status()
    except:
        st.warning(f"⚠️ تعذر جلب سوق {market}")
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
                "PE": float(d["d"][5]) if d["d"][5] else None
            })
        except:
            continue
    return pd.DataFrame(rows)

# =============================
# إشارات التداول
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
# إدارة الصفقات
# =============================
def analyze_trade(symbol, buy_price, quantity, market_df):
    current_row = market_df[market_df["Symbol"] == symbol]
    if current_row.empty:
        return {"Current Price": None, "Profit %": None, "Recommendation": "⚠️ غير موجود في السوق حالياً"}

    current_price = float(current_row["Price"].values[0])
    profit_percent = round((current_price - buy_price) / buy_price * 100, 2)

    if profit_percent >= 5:
        recommendation = "💰 بيع لتحقيق الربح"
    elif profit_percent <= -3:
        recommendation = "⚠️ بيع لتجنب الخسارة"
    else:
        recommendation = "🟢 استمرار"

    return {"Current Price": current_price, "Profit %": profit_percent, "Recommendation": recommendation}

def load_trades():
    try:
        return pd.read_csv(TRADES_FILE)
    except:
        return pd.DataFrame(columns=["Symbol", "Buy Price", "Quantity", "Date"])

def save_trade(symbol, buy_price, quantity):
    trades_df = load_trades()
    new_trade = pd.DataFrame([{
        "Symbol": symbol,
        "Buy Price": buy_price,
        "Quantity": quantity,
        "Date": datetime.now().strftime("%Y-%m-%d")
    }])
    trades_df = pd.concat([trades_df, new_trade], ignore_index=True)
    trades_df.to_csv(TRADES_FILE, index=False)

# =============================
# واجهة المستخدم
# =============================
st.title("📊 Market Dashboard")

# -----------------------------
# شريط التابات في الأعلى
# -----------------------------
page = st.radio("🔹 اختر التاب", ["فرص مضاربية", "أقوى الأسهم", "إدارة الصفقة", "تتبع الصفقات"], horizontal=True)

# -----------------------------
# فلتر السوق
# -----------------------------
market_choice = st.selectbox("اختر السوق", ["السعودي", "الأمريكي"])
with st.spinner(f"جلب بيانات سوق {market_choice}..."):
    df = fetch_market("ksa") if market_choice == "السعودي" else fetch_market("america")
df = add_signals(df)

# =============================
# تاب 1: فرص مضاربية
# =============================
if page == "فرص مضاربية":
    if df.empty:
        st.info("لا توجد بيانات حالياً")
    else:
        st.subheader("📊 فرص مضاربية")
        st.dataframe(df, use_container_width=True, hide_index=True)

# =============================
# تاب 2: أقوى الأسهم
# =============================
elif page == "أقوى الأسهم":
    strong_stocks = df[df["الحالة"] == "⭐ قوي للشراء"]
    if strong_stocks.empty:
        st.info("لا توجد فرص قوية حالياً")
    else:
        st.subheader("⭐ أقوى الأسهم قوة شرائية")
        st.dataframe(strong_stocks, use_container_width=True, hide_index=True)

# =============================
# تاب 3: إدارة الصفقة
# =============================
elif page == "إدارة الصفقة":
    st.subheader("💼 إدارة صفقة جديدة")
    symbol = st.text_input("رمز السهم")
    buy_price = st.number_input("سعر الشراء", min_value=0.0, step=0.01)
    quantity = st.number_input("عدد الأسهم", min_value=1, step=1)

    if st.button("💾 إضافة الصفقة"):
        if symbol and buy_price > 0 and quantity > 0:
            save_trade(symbol.upper(), buy_price, quantity)
            st.success(f"تم إضافة الصفقة {symbol.upper()}")
        else:
            st.warning("يرجى إدخال جميع البيانات")

# =============================
# تاب 4: تتبع الصفقات
# =============================
elif page == "تتبع الصفقات":
    trades_df = load_trades()
    if trades_df.empty:
        st.info("لا توجد صفقات حالياً")
    else:
        st.subheader("📈 تتبع الصفقات الحالية")
        results = []
        for _, trade in trades_df.iterrows():
            analysis = analyze_trade(trade["Symbol"], trade["Buy Price"], trade["Quantity"], df)
            results.append({
                "Symbol": trade["Symbol"],
                "Buy Price": trade["Buy Price"],
                "Quantity": trade["Quantity"],
                "Current Price": analysis["Current Price"],
                "Profit %": analysis["Profit %"],
                "Recommendation": analysis["Recommendation"],
                "Date": trade["Date"]
            })

            # تنبيهات تلقائية
            if analysis["Recommendation"] == "💰 بيع لتحقيق الربح":
                st.success(f"💹 الصفقة {trade['Symbol']}: حان وقت البيع لتحقيق الربح! (ربح {analysis['Profit %']}%)")
            elif analysis["Recommendation"] == "⚠️ بيع لتجنب الخسارة":
                st.error(f"⚠️ الصفقة {trade['Symbol']}: يجب البيع لتجنب الخسارة! (خسارة {analysis['Profit %']}%)")

        st.dataframe(pd.DataFrame(results), use_container_width=True, hide_index=True)
