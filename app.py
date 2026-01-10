import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="Realtime Stock Dashboard", layout="wide")
st.title("📊 Saudi & US Stocks Dashboard (Realtime)")

st_autorefresh(interval=60_000, key="datarefresh")

def fetch_tradingview(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(url, headers=headers)
    if res.status_code != 200:
        st.warning(f"⚠️ لا يمكن الوصول إلى {url}")
        return pd.DataFrame()
    
    soup = BeautifulSoup(res.text, "html.parser")
    data = []
    rows = soup.find_all("td", class_="cell-RLhfr_y4")
    for row in rows:
        try:
            symbol = row.find("a", class_="tickerName-GrtoTeat").text.strip()
            name = row.find("a", class_="tickerDescription-GrtoTeat").text.strip()
            price_tag = row.find_next_sibling("td", class_="cell-1xn2qvP4 right-1lRZ6ec")
            price = price_tag.text.strip() if price_tag else "N/A"
            change_tag = row.find_next_sibling("td", class_="cell-2snP2mJx right-1lRZ6ec")
            change = change_tag.text.strip().replace("%","") if change_tag else "0"
            data.append([symbol, name, price, change])
        except:
            continue
    df = pd.DataFrame(data, columns=["Symbol", "Name", "Price", "Change%"])
    return df

def classify_stock(change):
    try:
        change = float(change)
        if change >= 2: return "Strong Buy"
        elif 0.5 <= change < 2: return "Buy"
        elif -0.5 < change < 0.5: return "Neutral"
        elif -2 < change <= -0.5: return "Sell"
        elif change <= -2: return "Strong Sell"
    except:
        return "N/A"

st.sidebar.header("خيارات السوق")
market = st.sidebar.selectbox("اختر السوق", ["Saudi", "US", "Both"])
signal_filter = st.sidebar.multiselect(
    "فلترة حسب قوة السهم",
    ["Strong Buy", "Buy", "Neutral", "Sell", "Strong Sell"],
    default=["Strong Buy", "Buy", "Neutral", "Sell", "Strong Sell"]
)
search = st.sidebar.text_input("🔍 بحث عن سهم")

if "prev_strong_buy" not in st.session_state:
    st.session_state.prev_strong_buy = []

dfs = []
if market in ["Saudi", "Both"]:
    dfs.append(fetch_tradingview("https://ar.tradingview.com/markets/stocks-ksa/market-movers-all-stocks/"))
if market in ["US", "Both"]:
    dfs.append(fetch_tradingview("https://ar.tradingview.com/markets/stocks-usa/market-movers-all-stocks/"))

df = pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()

if not df.empty:
    df["Change%"] = pd.to_numeric(df["Change%"], errors="coerce").fillna(0)
    df["Signal"] = df["Change%"].apply(classify_stock)

    filtered_df = df[
        (df["Name"].str.contains(search, case=False)) | 
        (df["Symbol"].str.contains(search, case=False))
    ]
    filtered_df = filtered_df[filtered_df["Signal"].isin(signal_filter)]

    st.subheader(f"📋 الأسهم بعد الفلترة (تحديث: {datetime.now().strftime('%H:%M:%S')})")
    st.dataframe(filtered_df, use_container_width=True)

    st.subheader("🚀 أعلى 5 رابحة")
    st.table(df.sort_values("Change%", ascending=False).head(5)[["Symbol","Name","Price","Change%","Signal"]])

    st.subheader("📉 أعلى 5 خاسرة")
    st.table(df.sort_values("Change%", ascending=True).head(5)[["Symbol","Name","Price","Change%","Signal"]])

    current_strong_buy = df[df["Signal"]=="Strong Buy"]["Symbol"].tolist()
    new_alerts = [s for s in current_strong_buy if s not in st.session_state.prev_strong_buy]

    if new_alerts:
        st.success(f"🔔 فرص Strong Buy جديدة: {', '.join(new_alerts)}")
        st.audio("https://www.soundjay.com/button/beep-07.wav")

    st.session_state.prev_strong_buy = current_strong_buy

else:
    st.warning("⚠️ لا توجد بيانات حاليا.")
