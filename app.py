import streamlit as st
from bs4 import BeautifulSoup
import pandas as pd

# ---------- 1. HTML الجدول ----------
html_content = """ضع هنا الـ HTML الكامل للجدول"""

# ---------- 2. استخراج البيانات ----------
soup = BeautifulSoup(html_content, 'html.parser')
rows = soup.find_all('tr', class_='row-RdUXZpkv')

data = []
for row in rows:
    symbol_tag = row.find('a', class_='tickerName-GrtoTeat')
    company_tag = row.find('a', class_='tickerDescription-GrtoTeat')
    
    row_data = {}
    row_data['Symbol'] = symbol_tag.get_text(strip=True) if symbol_tag else ''
    row_data['Company'] = company_tag.get_text(strip=True) if company_tag else ''
    
    # إضافة بقية الأعمدة
    for td in row.find_all('td'):
        field = td.get('data-field')
        if not field:
            continue
        text = td.get_text(strip=True)
        row_data[field] = text
    
    if row_data:
        data.append(row_data)

df = pd.DataFrame(data)

# ---------- 3. تحويل الأعمدة الرقمية ----------
numeric_cols = ['Price', 'Change|TimeResolution1D', 'Volume|TimeResolution1D', 
                'RelativeVolume|TimeResolution1D', 'MarketCap', 
                'PriceToEarnings', 'EpsDiluted|ttm', 'EpsDilutedGrowth|YoYTTM', 
                'DividendsYield|ttm']

for col in numeric_cols:
    if col in df.columns:
        df[col] = df[col].str.replace('%','').str.replace(',','').str.replace('SAR','').astype(float, errors='ignore')

# ---------- 4. حساب عمود Signal ----------
def compute_signal(row):
    try:
        change = float(row.get('Change|TimeResolution1D', 0))
        eps_growth = float(row.get('EpsDilutedGrowth|YoYTTM', 0))
        pe_ratio = float(row.get('PriceToEarnings', 0))

        # قاعدة لتحديد الإشارة
        if change > 1 and eps_growth > 5 and pe_ratio < 20:
            return 'Buy'
        elif change < -1 and eps_growth < 0:
            return 'Sell'
        else:
            return 'Neutral'
    except:
        return 'Neutral'

df['Signal'] = df.apply(compute_signal, axis=1)

# ---------- 5. داشبورد Streamlit ----------
st.title("Stock Dashboard")

# تصفية حسب Signal
signal_filter = st.selectbox("عرض الأسهم حسب الإشارة:", ['All', 'Buy', 'Sell', 'Neutral'])
if signal_filter != 'All':
    df_display = df[df['Signal'] == signal_filter]
else:
    df_display = df

# ---------- 6. تلوين الصفوف ----------
def highlight_signal(row):
    color = ''
    if row['Signal'] == 'Buy':
        color = 'background-color: #b6f0b6'  # أخضر فاتح
    elif row['Signal'] == 'Sell':
        color = 'background-color: #f0b6b6'  # أحمر فاتح
    elif row['Signal'] == 'Neutral':
        color = 'background-color: #f0f0b6'  # أصفر فاتح
    return [color]*len(row)

# عرض الجدول مع التلوين
st.dataframe(df_display.style.apply(highlight_signal, axis=1))

# اختيار سهم لعرض التفاصيل
selected_symbol = st.selectbox("اختر السهم لعرض التفاصيل:", df_display['Symbol'])
if selected_symbol:
    st.write(df_display[df_display['Symbol'] == selected_symbol].T)  # عرض التفاصيل عمودياً
