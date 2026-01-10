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
            "Price": d["d"][2],
            "Change %": d["d"][3],
            "Relative Volume": d["d"][4],
            "PE": d["d"][5]
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
    strong_buy = (df["Change %"] > 2) & (df["Relative Volume"] > 1.5) & (df["PE"] < 30)
    potential_buy = ((df["Change %"] > 1) | (df["Relative Volume"] > 1.2)) & (df["PE"] < 50)

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
# واجهة المستخدم
# =============================
st.title("📊 Dashboard الفرص المضاربية")

# فلتر السوق
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

# عرض الجدول
st.dataframe(df, use_container_width=True, hide_index=True)
