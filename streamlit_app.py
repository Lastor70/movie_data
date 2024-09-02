import streamlit as st
import pandas as pd
import altair as alt
import data_fetcher
from datetime import datetime

# Налаштування сторінки
st.set_page_config(page_title="Present for volodik", page_icon="🎬")
st.title("Софт для Сладенького")
st.header('Таблиця замовлень:')

# Отримання ключа API з секретів
api_key = st.secrets["key"]

# Використання кешування для функції завантаження даних
@st.cache_data
def load_data(api_key):
    return data_fetcher.fetch_data(api_key)

# Функція для завантаження даних та збереження у session_state
def fetch_and_store_data():
    df_new = load_data(api_key)
    current_date = datetime.now().date()
    date = current_date.strftime('%Y-%m-%d')
    st.session_state['df_new'] = df_new
    st.session_state['date'] = date

# Кнопка для завантаження даних
if st.button('Завантажити дані'):
    fetch_and_store_data()
    st.success("Дані завантажено успішно!")

# Відображення даних, якщо вони вже завантажені
if 'df_new' in st.session_state:
    date = st.session_state.get('date', 'Невідома дата')
    st.write(f'Дані за {date}')
    st.dataframe(st.session_state['df_new'])
else:
    st.write("Натисніть кнопку для завантаження даних.")

# Секція для побудови графіка
st.subheader('Графік:')

# Перевіряємо, чи дані вже завантажені
if 'df_new' in st.session_state:
    df_new = st.session_state['df_new']

    # Вибір стовпців для графіка
    x_axis = st.selectbox(
        'Оберіть стовпець для осі X',
        options=df_new.columns,
        index=df_new.columns.get_loc("Номер замовлення") if "Номер замовлення" in df_new.columns else 0
    )
    y_axis = st.selectbox(
        'Оберіть стовпець для осі Y',
        options=df_new.columns,
        index=df_new.columns.get_loc("Загальна сума") if "Загальна сума" in df_new.columns else 1
    )

    # Побудова графіка за допомогою Altair
    chart = alt.Chart(df_new).mark_bar().encode(
        x=alt.X(x_axis, sort=None),
        y=y_axis,
        tooltip=[x_axis, y_axis]
    ).interactive()

    st.altair_chart(chart, use_container_width=True)
else:
    st.write("Завантажте дані для побудови графіка.")
