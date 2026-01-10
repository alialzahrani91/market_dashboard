import streamlit as st
import pandas as pd
import yfinance as yf

# ---------------------------
# 1️⃣ دالة لجلب البيانات
# ---------------------------
def fetch_market(market):
    if market == "saudi":
        tickers = ["1010.SR", "1050.SR"]  # ضع رموز السوق السعودي هنا
    elif market == "usa":
        tickers = ["AAPL", "TSLA"]       # ضع رموز السوق الأمريكي هنا
    else:
        tickers = []
    
    data_list = []
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            data_list.append({
                "رمز": ticker,
                "اسم": info.get("shortName", "N/A"),
                "Price": info.get("regularMarketPrice", 0),
                "إشارة": "🔥 شراء" if info.get("regularMarketChangePercent", 0) > 0 else "⚡ مراقبة",
                "Market": "السوق السعودي" if market=="saudi" else "السوق الأمريكي"
            })
        except Exception as e:
            st.error(f"خطأ في جلب {ticker}: {e}")
    
    return pd.DataFrame(data_list)

# ---------------------------
# 2️⃣ دالة لتحديد المضاربة
# ---------------------------
def add_signal(df):
    df["مضاربي"] = df["إشارة"].apply(lambda x: True if x == "🔥 شراء" else False)
    return df

# ---------------------------
# 3️⃣ دالة لحساب سعر الدخول وسعر الجني
# ---------------------------
def add_entry_takeprofit(df):
    df["سعر الدخول"] = df["Price"] * 0.995  # 0.5% أقل من السعر الحالي
    df["سعر الجني"]  = df["Price"] * 1.03   # 3% أعلى من السعر الحالي
    return df

# ---------------------------
# 4️⃣ واجهة Streamlit
# ---------------------------
st.set_page_config(page_title="Market Dashboard", layout="wide")
st.title("📊 لوحة بيانات السوق")

# الفلاتر في Sidebar
st.sidebar.title("🎛️ الفلاتر")
market_filter = st.sidebar.selectbox(
    "اختر السوق",
    ["الكل", "السوق السعودي", "السوق الأمريكي"]
)
speculative_only = st.sidebar.checkbox("💥 عرض المضاربة فقط")

# جلب البيانات
saudi = fetch_market("saudi")
usa = fetch_market("usa")
df = pd.concat([saudi, usa], ignore_index=True)

# إضافة تصنيف المضاربة وأسعار الدخول والجني
df = add_signal(df)
df = add_entry_takeprofit(df)

# تطبيق فلتر السوق
if market_filter != "الكل":
    df = df[df["Market"] == market_filter]

# تطبيق فلتر المضاربة فقط
if speculative_only:
    df = df[df["مضاربي"] == True]

# ترتيب الأعمدة للعرض
df = df[["رمز", "اسم", "Price", "إشارة", "مضاربي", "سعر الدخول", "سعر الجني", "Market"]]

# عرض الجدول
st.dataframe(df)
