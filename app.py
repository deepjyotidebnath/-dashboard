import re
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Expense Tracker", page_icon="💰")
st.title("💰 Expense Tracker Dashboard")
st.caption("Upload a bank statement CSV, get auto-categorized spending and trend charts.")

CATEGORY_RULES = {
    "Food & Dining": ["restaurant", "cafe", "coffee", "swiggy", "zomato", "starbucks", "mcdonald", "food"],
    "Groceries": ["grocery", "supermarket", "bigbasket", "reliance fresh", "dmart"],
    "Transport": ["uber", "ola", "petrol", "fuel", "metro", "taxi", "irctc"],
    "Shopping": ["amazon", "flipkart", "myntra", "mall", "shopping"],
    "Bills & Utilities": ["electricity", "water bill", "recharge", "broadband", "wifi", "gas bill"],
    "Entertainment": ["netflix", "spotify", "prime video", "movie", "bookmyshow", "hotstar"],
    "Rent": ["rent"],
    "Health": ["pharmacy", "hospital", "clinic", "medical", "doctor"],
    "Income": ["salary", "credited", "refund", "cashback"],
}


def categorize(description: str) -> str:
    desc = str(description).lower()
    for category, keywords in CATEGORY_RULES.items():
        if any(re.search(kw, desc) for kw in keywords):
            return category
    return "Other"


uploaded_file = st.sidebar.file_uploader("Upload bank statement CSV", type=["csv"])

st.sidebar.markdown("**Expected columns:** `date`, `description`, `amount`")
st.sidebar.caption("Column names are matched loosely — e.g. 'Transaction Date', 'Narration', 'Debit' all work.")

if uploaded_file is None:
    st.info("👈 Upload a CSV to get started.")
    st.stop()

df = pd.read_csv(uploaded_file)
df.columns = [c.strip().lower() for c in df.columns]

# loose column matching
date_col = next((c for c in df.columns if "date" in c), None)
desc_col = next((c for c in df.columns if any(k in c for k in ["desc", "narration", "particular"])), None)
amount_col = next((c for c in df.columns if any(k in c for k in ["amount", "debit", "withdrawal"])), None)

if not all([date_col, desc_col, amount_col]):
    st.error("Couldn't find date/description/amount columns. Rename headers and try again.")
    st.dataframe(df.head())
    st.stop()

df = df.rename(columns={date_col: "date", desc_col: "description", amount_col: "amount"})
df["date"] = pd.to_datetime(df["date"], errors="coerce")
df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
df = df.dropna(subset=["date", "amount"])
df["category"] = df["description"].apply(categorize)
df["month"] = df["date"].dt.to_period("M").astype(str)

spending = df[df["category"] != "Income"]

st.subheader("Overview")
col1, col2, col3 = st.columns(3)
col1.metric("Total Spent", f"₹{spending['amount'].sum():,.0f}")
col2.metric("Total Income", f"₹{df[df['category'] == 'Income']['amount'].sum():,.0f}")
col3.metric("Transactions", len(df))

st.subheader("Spending by Category")
by_category = spending.groupby("category")["amount"].sum().sort_values(ascending=False)
st.bar_chart(by_category)

st.subheader("Monthly Trend")
by_month = spending.groupby("month")["amount"].sum()
st.line_chart(by_month)

st.subheader("Transactions")
category_filter = st.multiselect("Filter by category", options=sorted(df["category"].unique()))
filtered = df[df["category"].isin(category_filter)] if category_filter else df
st.dataframe(
    filtered[["date", "description", "amount", "category"]].sort_values("date", ascending=False),
    use_container_width=True,
)