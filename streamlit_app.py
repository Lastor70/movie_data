import streamlit as st
import pandas as pd
import data_fetcher
from datetime import datetime

st.set_page_config(page_title="Present for volodik", page_icon="🎬")
st.title("Софт для Сладенького")
st.header('Таблиця замовлень:')
st.subheader('Графік:')

current_date = datetime.now().date()
date = current_date.strftime('%Y-%m-%d')
api_key = st.secrets["key"]

@st.cache_data
def load_data(api_key):
    return data_fetcher.fetch_data(api_key)

# Кнопка для завантаження даних
if st.button('Завантажити дані'):
    df_new = load_data(api_key)
    st.write(f'Данные за {date}')
    st.dataframe(df_new)
else:
    st.write("Натисніть кнопку для завантаження даних.")


print('s')