import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import hashlib

# ===== حماية Dashboard بكلمة مرور =====
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
st.title("📊 Market Scanner Dashboard - Saudi & US Stocks")

# ===== دالة جلب الأسهم وفصل الرمز عن الاسم =====
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
        if len(cells) >= 2:
            symbol = cells[0].get_text(strip=True) + suffix
            name = cells[1].get_text(strip=True)
            symbols.append({"symbol": symbol, "name": name})
        elif len(cells) == 1:
            parts = cells[0].get_text(strip=True).split(".")
            symb
