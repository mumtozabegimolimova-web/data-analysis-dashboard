import streamlit as st
from main import load_data, merge_data, prepare_data, calculate_metrics

st.set_page_config(page_title="Book Dashboard", layout="wide")

st.title("📊 Book Sales Dashboard")

# выбор датасета
dataset = st.selectbox("Choose dataset", ["DATA1", "DATA2", "DATA3"])
path = f"data/{dataset}"

# загрузка и обработка
users, orders, books = load_data(path)
df = merge_data(users, orders, books)
df = prepare_data(df)

# метрики
top5, unique_users, author_sets, popular_author, top_customer, daily = calculate_metrics(df)

# UI
col1, col2, col3 = st.columns(3)

col1.metric("👤 Unique Users", f"{unique_users:,}")
col2.metric("📚 Author Sets", author_sets)
col3.metric("🏆 Top Customer", f"${top_customer:.2f}")

st.subheader("💰 Top 5 Days (by daily revenue)")
st.dataframe(top5)

st.subheader("✍️ Most Popular Author")
st.write(popular_author[0])  # убираем ('name',)

st.subheader("📈 Daily Revenue Trend")
st.line_chart(daily)