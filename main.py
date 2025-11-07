import streamlit as st
import pandas as pd

# ----------------------------
# PAGE CONFIG
# ----------------------------
st.set_page_config(page_title="Dairy Farm Management", layout="wide")

# ----------------------------
# GOOGLE SHEET IDS FROM SECRETS
# ----------------------------
INVESTMENT_SHEET_ID = st.secrets["sheets"]["INVESTMENT_SHEET_ID"]
MILK_DIS_M_SHEET_ID = st.secrets["sheets"]["MILK_DIS_M_SHEET_ID"]
MILK_DIS_E_SHEET_ID = st.secrets["sheets"]["MILK_DIS_E_SHEET_ID"]
EXPENSE_SHEET_ID = st.secrets["sheets"]["EXPENSE_SHEET_ID"]
COW_LOG_SHEET_ID = st.secrets["sheets"]["COW_LOG_SHEET_ID"]
PAYMENT_SHEET_ID = st.secrets["sheets"]["PAYMENT_SHEET_ID"]

# ----------------------------
# SHEET NAMES & URLs
# ----------------------------
INVESTMENT_CSV_URL = f"https://docs.google.com/spreadsheets/d/{INVESTMENT_SHEET_ID}/gviz/tq?tqx=out:csv&sheet=investment"
MILK_DIS_M_CSV_URL = f"https://docs.google.com/spreadsheets/d/{MILK_DIS_M_SHEET_ID}/gviz/tq?tqx=out:csv&sheet=morning"
MILK_DIS_E_CSV_URL = f"https://docs.google.com/spreadsheets/d/{MILK_DIS_E_SHEET_ID}/gviz/tq?tqx=out:csv&sheet=evening"
EXPENSE_CSV_URL = f"https://docs.google.com/spreadsheets/d/{EXPENSE_SHEET_ID}/gviz/tq?tqx=out:csv&sheet=expense"
COW_LOG_CSV_URL = f"https://docs.google.com/spreadsheets/d/{COW_LOG_SHEET_ID}/gviz/tq?tqx=out:csv&sheet=dailylog"
PAYMENT_CSV_URL = f"https://docs.google.com/spreadsheets/d/{PAYMENT_SHEET_ID}/gviz/tq?tqx=out:csv&sheet=payment"

# ----------------------------
# DATA LOADING FUNCTION
# ----------------------------
@st.cache_data(ttl=600)
def load_csv(url, drop_cols=None):
    try:
        df = pd.read_csv(url)
        if drop_cols:
            df = df.drop(columns=[col for col in drop_cols if col in df.columns])
        return df
    except Exception as e:
        st.error(f"❌ Failed to load data from Google Sheet: {e}")
        return pd.DataFrame()

def sum_numeric_columns(df, exclude_cols=None):
    if df.empty:
        return 0
    if exclude_cols is None:
        exclude_cols = []
    numeric_cols = [col for col in df.columns if col not in exclude_cols]
    df_numeric = df[numeric_cols].apply(pd.to_numeric, errors="coerce")
    return df_numeric.sum().sum()

# ----------------------------
# SIDEBAR NAVIGATION
# ----------------------------
st.sidebar.header("Navigation")
page = st.sidebar.radio(
    "Go to",
    ["🏠 Dashboard", "Milking & Feeding", "Milk Distribution", "Expense", "Payments", "Investments"]
)

# ----------------------------
# DASHBOARD
# ----------------------------
if page == "🏠 Dashboard":
    st.title("📊 Dairy Farm Dashboard")
    st.caption("Overview of total performance and key farm metrics.")

    df_expense = load_csv(EXPENSE_CSV_URL, drop_cols=["Timestamp"])
    df_invest = load_csv(INVESTMENT_CSV_URL, drop_cols=["Timestamp"])
    df_payment = load_csv(PAYMENT_CSV_URL, drop_cols=["Timestamp"])
    df_milk_m = load_csv(MILK_DIS_M_CSV_URL, drop_cols=["Timestamp"])
    df_milk_e = load_csv(MILK_DIS_E_CSV_URL, drop_cols=["Timestamp"])
    df_cow_log = load_csv(COW_LOG_CSV_URL, drop_cols=["Timestamp"])

    total_expense = df_expense["Amount"].sum() if "Amount" in df_expense.columns else 0
    total_invest = df_invest["Amount"].sum() if "Amount" in df_invest.columns else 0
    total_payment = df_payment["Amount"].sum() if "Amount" in df_payment.columns else 0
    total_milk_m = sum_numeric_columns(df_milk_m, exclude_cols=["Timestamp", "Date"])
    total_milk_e = sum_numeric_columns(df_milk_e, exclude_cols=["Timestamp", "Date"])
    total_milk = total_milk_m + total_milk_e

    col1, col2, col3 = st.columns(3)
    col1.metric("💸 Total Expenses", f"₹{total_expense:,.2f}")
    col2.metric("📈 Total Investment", f"₹{total_invest:,.2f}")
    col3.metric("💰 Total Payments", f"₹{total_payment:,.2f}")

    col4, col5 = st.columns(2)
    col4.metric("🥛 Total Milk Distributed", f"{total_milk:.2f} L")
    col5.metric("🌅 Morning Milk", f"{total_milk_m:.2f} L")
    col5.metric("🌇 Evening Milk", f"{total_milk_e:.2f} L")

    # ---- TOTAL MILKING DATA ----
    st.divider()
    st.subheader("🐄 Milk Production Summary (from Milking & Feeding Log)")
    if not df_cow_log.empty:
        df_cow_log.columns = [c.strip().lower() for c in df_cow_log.columns]
        if "date" in df_cow_log.columns and "milking -दूध" in df_cow_log.columns:
            df_cow_log["date"] = pd.to_datetime(df_cow_log["date"], errors="coerce")
            df_cow_log["milking -दूध"] = pd.to_numeric(df_cow_log["milking -दूध"], errors="coerce")
            milk_per_day = df_cow_log.groupby("date")["milking -दूध"].sum().reset_index()
            total_milk_produced = milk_per_day["milking -दूध"].sum()

            colA, colB = st.columns(2)
            colA.metric("Total Milk Produced", f"{total_milk_produced:.2f} L")
            colB.metric("Number of Days Recorded", f"{len(milk_per_day)} days")

            st.line_chart(milk_per_day.set_index("date"))
        else:
            st.warning("⚠️ 'Date' or 'Milking -दूध' column not found in cow log sheet.")

    # ---- FUND ----
    st.divider()
    st.subheader("💼 Fund Summary")
    bipin_invest = df_invest[df_invest["Paid To"].str.contains("Bipin Kumar", case=False, na=False)] if "Paid To" in df_invest.columns else pd.DataFrame()
    bipin_payment = df_payment[df_payment["Received By"].str.contains("Bipin Kumar", case=False, na=False)] if "Received By" in df_payment.columns else pd.DataFrame()
    bipin_expense = df_expense[df_expense["Expense By"].str.contains("Bipin Kumar", case=False, na=False)] if "Expense By" in df_expense.columns else pd.DataFrame()

    fund_bipin = (
        bipin_invest["Amount"].sum() +
        bipin_payment["Amount"].sum() -
        bipin_expense["Amount"].sum()
    )
    st.metric("Fund Available at Bipin Kumar", f"₹{fund_bipin:,.2f}")

# ----------------------------
# MILKING & FEEDING PAGE
# ----------------------------
elif page == "Milking & Feeding":
    st.title("🐄 Milking & Feeding Log")
    st.caption("Daily cow log data including milk quantity, feed, and health details.")
    df = load_csv(COW_LOG_CSV_URL, drop_cols=["Timestamp"])

    if not df.empty:
        if "Date" in df.columns:
            df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
            df = df.sort_values("Date", ascending=False)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No milking & feeding data available yet.")

    if not df.empty:
        df.columns = [c.strip().lower() for c in df.columns]
        if "date" in df.columns and "cowid" in df.columns and "milking -दूध" in df.columns:
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
            df["milking -दूध"] = pd.to_numeric(df["milking -दूध"], errors="coerce")
            daily_cow = df.groupby(["date", "cowid"])["milking -दूध"].sum().reset_index()
            st.dataframe(daily_cow, use_container_width=True)

            st.bar_chart(daily_cow.pivot(index="date", columns="cowid", values="milking -दूध"))
        else:
            st.warning("⚠️ Required columns ('Date', 'CowID', 'Milking -दूध') not found.")
    else:
        st.info("No milking & feeding data available yet.")

# ----------------------------
# MILK DISTRIBUTION PAGE
# ----------------------------
elif page == "Milk Distribution":
    st.title("🥛 Milk Distribution")
    df_morning = load_csv(MILK_DIS_M_CSV_URL, drop_cols=["Timestamp"])
    df_evening = load_csv(MILK_DIS_E_CSV_URL, drop_cols=["Timestamp"])
    df_cow_log = load_csv(COW_LOG_CSV_URL, drop_cols=["Timestamp"])

    # Display raw data
    st.subheader("Morning Distribution")
    st.dataframe(df_morning, use_container_width=True)
    st.subheader("Evening Distribution")
    st.dataframe(df_evening, use_container_width=True)

    # --- Daily totals ---
    st.divider()
    st.subheader("📅 Daily Milk Distribution & Validation")

    try:
        for df_ in [df_morning, df_evening]:
            df_.columns = [c.strip().lower() for c in df_.columns]
            df_["date"] = pd.to_datetime(df_["date"], errors="coerce")

        df_morning_total = df_morning.groupby("date").sum(numeric_only=True).reset_index()
        df_evening_total = df_evening.groupby("date").sum(numeric_only=True).reset_index()
        dist = pd.merge(df_morning_total, df_evening_total, on="date", how="outer").fillna(0)
        dist["distributed_total"] = dist.drop(columns=["date"]).sum(axis=1)

        # --- Produced vs Distributed ---
        df_cow_log.columns = [c.strip().lower() for c in df_cow_log.columns]
        df_cow_log["date"] = pd.to_datetime(df_cow_log["date"], errors="coerce")
        df_cow_log["milking -दूध"] = pd.to_numeric(df_cow_log["milking -दूध"], errors="coerce")
        produced = df_cow_log.groupby("date")["milking -दूध"].sum().reset_index()
        compare = pd.merge(produced, dist[["date", "distributed_total"]], on="date", how="outer").fillna(0)
        compare["remaining/loss"] = compare["milking -दूध"] - compare["distributed_total"]

        st.dataframe(compare, use_container_width=True)
        st.bar_chart(compare.set_index("date")[["milking -दूध", "distributed_total", "remaining/loss"]])

    except Exception as e:
        st.warning(f"⚠️ Could not calculate distribution validation: {e}")

# ----------------------------
# EXPENSE, PAYMENTS, INVESTMENTS (unchanged)
# ----------------------------
elif page == "Expense":
    st.title("💸 Expense Tracker")

    df_expense = load_csv(EXPENSE_CSV_URL, drop_cols=["Timestamp"])

    if not df_expense.empty:
        # --- Convert Date column properly ---
        if "Date" in df_expense.columns:
            df_expense["Date"] = pd.to_datetime(df_expense["Date"], errors="coerce")
            df_expense = df_expense.sort_values("Date", ascending=False)

        # --- Total Expense ---
        total_expense = df_expense["Amount"].sum()

        # --- Current Month Expense ---
        current_month = pd.Timestamp.now().month
        current_year = pd.Timestamp.now().year
        df_this_month = df_expense[
            (df_expense["Date"].dt.month == current_month)
            & (df_expense["Date"].dt.year == current_year)
        ]
        monthly_expense = df_this_month["Amount"].sum()

        # --- KPIs ---
        col1, col2 = st.columns(2)
        col1.metric("💰 Total Expense", f"₹{total_expense:,.2f}")
        col2.metric("📅 This Month's Expense", f"₹{monthly_expense:,.2f}")

        st.divider()

        # --- Expense by Type ---
        if "Expense Type" in df_expense.columns:
            expense_by_type = (
                df_expense.groupby("Expense Type")["Amount"].sum().sort_values(ascending=False)
            )
            st.subheader("📊 Expense by Type")
            st.bar_chart(expense_by_type)

        # --- Expense by Person ---
        if "Expense By" in df_expense.columns:
            expense_by_person = (
                df_expense.groupby("Expense By")["Amount"].sum().sort_values(ascending=False)
            )
            st.subheader("👤 Expense by Person")
            st.bar_chart(expense_by_person)

        st.divider()
        st.subheader("🧾 Detailed Expense Records")
        st.dataframe(df_expense, use_container_width=True)

    else:
        st.info("No expense records found.")


elif page == "Payments":
    st.title("💰 Payments Record")
    df_payment = load_csv(PAYMENT_CSV_URL, drop_cols=["Timestamp"])
    st.dataframe(df_payment, use_container_width=True if not df_payment.empty else False)

elif page == "Investments":
    st.title("📈 Investment Log")
    df_invest = load_csv(INVESTMENT_CSV_URL, drop_cols=["Timestamp"])
    st.dataframe(df_invest, use_container_width=True if not df_invest.empty else False)

# ----------------------------
# REFRESH BUTTON
# ----------------------------
if st.sidebar.button("🔁 Refresh"):
    st.rerun()
