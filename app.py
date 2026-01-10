import streamlit as st
import requests
from bs4 import BeautifulSoup
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="Stock Dashboard", layout="wide")
st.title("📊 سوق الأسهم - السعودية و أمريكا")

# ======================
# دالة لجلب الرموز والأسماء من TradingView
# ======================
@st.cache_data(ttl=24*3600)
def get_symbols_tradingview(url, suffix=""):
    res = requests.get(url)
    if res.status_code != 200:
        st.warning(f"⚠️ تعذر جلب الأسهم من {url}")
        return []

    soup = BeautifulSoup(res.text, "html.parser")
    symbols = []

    for row in soup.select("table tbody tr"):
        cell = row.find("td", class_="cell-RLhfr_y4")
        if cell:
            symbol_tag = cell.find("a", class_="tickerName-GrtoTeat")
            name_tag = cell.find("a", class_="tickerDescription-GrtoTeat")
            if symbol_tag and name_tag:
                symbol = symbol_tag.text.strip() + suffix
                name = name_tag.text.strip()
                symbols.append({"symbol": symbol, "name": name})

    return symbols

# ======================
# جلب الأسهم
# ======================
st.info("🔄 جلب الأسهم من TradingView...")
saudi_symbols = get_symbols_tradingview(
    "https://ar.tradingview.com/markets/stocks-ksa/market-movers-all-stocks/",
    ".TADAWUL"
)
us_symbols = get_symbols_tradingview(
    "https://ar.tradingview.com/markets/stocks-usa/market-movers-all-stocks/"
)

all_symbols = saudi_symbols + us_symbols

if not all_symbols:
    st.error("⚠️ تعذر جلب أي أسهم.")
    st.stop()

# ======================
# جدول DataFrame للعرض
# ======================
df = pd.DataFrame(all_symbols)
df["Price"] = ""  # عمود فارغ للسعر

# ======================
# جلب الأسعار الحالية باستخدام yfinance
# ======================
st.info("💹 جلب الأسعار الحالية للأسهم...")
for i, row in df.iterrows():
    try:
        ticker = yf.Ticker(row["symbol"])
        price = ticker.history(period="1d")["Close"].iloc[-1]
        df.at[i, "Price"] = round(price, 2)
    except Exception as e:
        df.at[i, "Price"] = "N/A"

# ======================
# فلترة وواجهة Dashboard
# ======================
st.subheader("قائمة الأسهم")
st.dataframe(df, use_container_width=True)

st.success(f"✅ تم جلب {len(df)} سهم بنجاح!")
