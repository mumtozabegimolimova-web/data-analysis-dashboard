import pandas as pd
import os
import yaml
import re
import matplotlib.pyplot as plt

def analyze_dataset(path):
    users, orders, books = load_data(path)

    df = merge_data(users, orders, books)
    df = prepare_data(df)

    df = df[df["paid_price"] < df["paid_price"].quantile(0.99)]

    top5 = get_top5_days(df)
    unique_users = get_unique_users(df)
    author_sets = get_author_sets(df)
    popular_author = get_most_popular_author(df)
    top_customer = get_top_customer(df)

    daily = df.groupby("date")["paid_price"].sum()

    return {
        "top5": top5,
        "unique_users": unique_users,
        "author_sets": author_sets,
        "popular_author": popular_author,
        "top_customer": top_customer,
        "daily": daily
    }

DATA_PATH = "data/DATA1"


# ---------- LOAD ----------
def load_data(path):
    users = pd.read_csv(os.path.join(path, "users.csv"))
    orders = pd.read_parquet(os.path.join(path, "orders.parquet"))

    with open(os.path.join(path, "books.yaml"), "r") as f:
        books = yaml.safe_load(f)

    books = pd.json_normalize(books)

    return users, orders, books


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


# ---------- MERGE ----------
def merge_data(users, orders, books):
    books.columns = books.columns.str.replace(":", "")

    df = orders.merge(users, left_on="user_id", right_on="id", how="left")
    df = df.merge(books, left_on="book_id", right_on="id", how="left")

    return df


# ---------- PREPARE ----------
def prepare_data(df):
    df["timestamp"] = df["timestamp"].astype(str)

# убираем точки в AM/PM
    df["timestamp"] = df["timestamp"].str.replace("A.M.", "AM", regex=False)
    df["timestamp"] = df["timestamp"].str.replace("P.M.", "PM", regex=False)

# универсальный парсинг
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")   

# дата
    df = df.dropna(subset=["timestamp"])
    df["date"] = df["timestamp"].dt.date

    # --- CLEAN NUMBERS ---
    df["unit_price"] = df["unit_price"].apply(clean_price)
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")

    df = df.dropna(subset=["unit_price", "quantity"])

    # --- CALCULATE ---
    df["paid_price"] = df["quantity"] * df["unit_price"]

    return df


# ---------- METRICS ----------
def get_metrics(df):
    # дневная выручка
    daily = df.groupby("date")["paid_price"].sum()

    # топ 5 дней
    top5 = daily.sort_values(ascending=False).head(5).round(2)

    return daily, top5


# ---------- METRICS ----------
def get_top5_days(df):
    daily = df.groupby("date")["paid_price"].sum()
    return daily.sort_values(ascending=False).head(5).round(2)

# ---------- MAIN ----------
def main():
    users, orders, books = load_data(DATA_PATH)

    df = merge_data(users, orders, books)
    df = prepare_data(df)

    print("Data prepared ✅")

    top5 = get_top5_days(df)

    print("\nTop 5 days:")
    print(top5)

    unique_users = get_unique_users(df)
    print("\nUnique users:", unique_users)

    author_sets = get_author_sets(df)
    print("\nAuthor sets:", author_sets)

    popular_author = get_most_popular_author(df)
    print("\nMost popular author:", popular_author)

    top_customer = get_top_customer(df)
    print("\nTop customer:", top_customer)

    plot_daily_revenue(df)

def get_unique_users(df):
    df["user_key"] = (
        df[["email", "phone", "address"]]
        .fillna("")  # 👈 ВАЖНО
        .astype(str)
        .agg("-".join, axis=1)
    )
    return df["user_key"].nunique()

def get_author_sets(df):
    df["author_set"] = df["author"].apply(
        lambda x: tuple(sorted(x)) if isinstance(x, list) else (x,)
    )
    return df["author_set"].nunique()

def get_most_popular_author(df):
    df["author_set"] = df["author"].apply(
        lambda x: tuple(sorted(x)) if isinstance(x, list) else (x,)
    )
    return df.groupby("author_set")["quantity"].sum().idxmax()

def get_top_customer(df):
    spending = df.groupby("user_id")["paid_price"].sum()
    return spending.idxmax()

def plot_daily_revenue(df):
    daily = df.groupby("date")["paid_price"].sum()

    plt.figure()
    daily.plot()
    plt.title("Daily Revenue")
    plt.xlabel("Date")
    plt.ylabel("Revenue")
    plt.show()

def calculate_metrics(df):
    unique_users = df["user_id"].nunique()
    author_sets = df["author"].nunique()

    popular_author = df["author"].mode()

    top_customer = df.groupby("user_id")["paid_price"].sum().max()

    df["date"] = df["timestamp"].dt.date

    daily = df.groupby("date")["paid_price"].sum()

    top5 = daily.sort_values(ascending=False).head(5)

    return top5, unique_users, author_sets, popular_author, top_customer, daily
