import streamlit as st
import pandas as pd
import os
import yaml
import re

DATA_PATH = "data/DATA1"

# ---------- CLEAN PRICE ----------
def clean_price(price):
    if pd.isna(price):
        return None

    price = str(price)
    is_eur = "€" in price or "EUR" in price

    price = price.replace(",", ".")
    match = re.search(r"\d+(\.\d+)?", price)

    if not match:
        return None

    value = float(match.group())

    if is_eur:
        value *= 1.2

    return value


# ---------- LOAD ----------
@st.cache_data
def load_data():
    users = pd.read_csv(os.path.join(DATA_PATH, "users.csv"))
    orders = pd.read_parquet(os.path.join(DATA_PATH, "orders.parquet"))

    with open(os.path.join(DATA_PATH, "books.yaml"), "r") as f:
        books = yaml.safe_load(f)

    books = pd.json_normalize(books)
    books.columns = books.columns.str.replace(":", "")

    return users, orders, books


# ---------- PREPARE ----------
@st.cache_data
def prepare():
    users, orders, books = load_data()

    df = orders.merge(users, left_on="user_id", right_on="id", how="left")
    df = df.merge(books, left_on="book_id", right_on="id", how="left")

    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce", utc=True)
    df["timestamp"] = df["timestamp"].dt.tz_localize(None)

    df["unit_price"] = df["unit_price"].apply(clean_price)
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")

    df = df.dropna(subset=["unit_price", "quantity"])

    df["paid_price"] = df["quantity"] * df["unit_price"]
    df["date"] = df["timestamp"].dt.date

    return df


# ---------- CALCULATIONS ----------
def calculate_metrics(df):
    daily = df.groupby("date")["paid_price"].sum()
    top5 = daily.sort_values(ascending=False).head(5).round(2)

    unique_users = (
        df[["email", "phone", "address"]]
        .fillna("")
        .astype(str)
        .agg("-".join, axis=1)
        .nunique()
    )

    df["author_set"] = df["author"].apply(
        lambda x: tuple(sorted(x)) if isinstance(x, list) else (x,)
    )

    author_sets = df["author_set"].nunique()
    popular_author = df.groupby("author_set")["quantity"].sum().idxmax()

    top_customer = df.groupby("user_id")["paid_price"].sum().idxmax()

    return top5, unique_users, author_sets, popular_author, top_customer, daily


# ---------- UI ----------
st.set_page_config(page_title="Book Dashboard", layout="wide")

st.title("📊 Book Sales Dashboard")

df = prepare()
top5, unique_users, author_sets, popular_author, top_customer, daily = calculate_metrics(df)

col1, col2, col3 = st.columns(3)

col1.metric("👤 Unique Users", unique_users)
col2.metric("📚 Author Sets", author_sets)
col3.metric("🏆 Top Customer", top_customer)

st.subheader("💰 Top 5 Days by Revenue")
st.dataframe(top5)

st.subheader("✍️ Most Popular Author")
st.write(popular_author)

st.subheader("📈 Daily Revenue")
st.line_chart(daily)