import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import hashlib

# ===== حماية بكلمة مرور =====
PASSWORD_HASH = hashlib.sha256("mypassword123".encode()).hexdigest()
def check_password():
    st.sidebar.header("🔐 تسجيل الدخول")
    password = st.sidebar.text_input("كلمة المرور", type="password")
    if hashlib.sha256(password.encode()).hexdigest() == PASSWORD_HASH:
        return True
    return False

if not check_password():
    st.warning("❌ كلمة المرور غير صحيحة")
    st.stop()

st.set_page_config(page_title="Market Scanner", layout="wide")
st.title("📊 Market Scanner Dashboard - Saudi & US Stocks from TradingView")

# ===== دوال جلب الأسهم من TradingView =====
@st.cache_data(ttl=24*3600)
def get_symbols(url, suffix=""):
    res = requests.get(url)
    if res.status_code != 200:
        st.warning(f"⚠️ تعذر جلب الأسهم من {url}")
        return []

    soup = BeautifulSoup(res.text, "html.parser")
    symbols = []
    for row in soup.select("table tbody tr"):
        cells = row.find_all("td")
        if len(cells) > 0:
            symbol_text = cells[0].get_text(strip=True)
            symbols.append(symbol_text + suffix)
    return symbols

def get_saudi_symbols():
    return get_symbols("https://ar.tradingview.com/markets/stocks-ksa/market-movers-all-stocks/", ".TADAWUL")

def get_us_symbols():
    return get_symbols("p")

# ===== اختيار السوق =====
market = st.selectbox("اختر السوق", ["السعودي", "الأمريكي", "الكل"])

symbols = []
if market == "السعودي":
    symbols = get_saudi_symbols()
elif market == "الأمريكي":
    symbols = get_us_symbols()
else:
    symbols = get_saudi_symbols() + get_us_symbols()

st.info(f"⏳ جاري تحضير قائمة {len(symbols)} سهم من {market}...")

# ===== إعداد جدول النتائج الأساسي =====
results = []
for symbol in symbols:
    # حسابات تقريبية (كمثال)
    entry = None
    stop = None
    target1 = None
    target2 = None
    rating = "⭐"  # هنا يمكن إضافة خوارزميات بسيطة لاحقًا

    results.append({
        "symbol": symbol,
        "rating": rating,
        "entry": entry,
        "stop": stop,
        "target_1": target1,
        "target_2": target2
    })

# ===== عرض النتائج =====
if results:
    df_results = pd.DataFrame(results)
    st.dataframe(df_results, use_container_width=True)
else:
    st.warning("❌ لم يتم العثور على أي أسهم حالياً")
