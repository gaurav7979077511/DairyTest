import streamlit as st
import pandas as pd
import plotly.express as px

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


if page == "Dashboard":
    # ------------------------------
    # CUSTOM CSS (Dark + Light Mode)
    # ------------------------------
    st.markdown("""
        <style>
        [data-testid="stAppViewContainer"] {
            background-color: var(--background-color, #121212);
            color: var(--text-color, #e0e0e0);
        }
        .block-container {
            background: rgba(30, 30, 30, 0.95);
            padding: 1.5rem;
            border-radius: 20px;
            box-shadow: 0 0 15px rgba(0,0,0,0.4);
        }
        div[data-testid="stMetricValue"] {
            color: var(--text-color, #e0e0e0);
            font-weight: 600;
        }
        .radio-center {
            display: flex;
            justify-content: center;
            align-items: center;
            width: 100%;
        }
        div[data-testid="stHorizontalBlock"] > div[role="radiogroup"] {
            justify-content: center !important;
            display: flex !important;
            flex-wrap: wrap;
            gap: 0.75rem;
        }
        div[data-testid="stRadio"] label {
            color: var(--text-color, #e0e0e0) !important;
            font-weight: 500;
        }
        div[data-testid="stRadio"] {
            text-align: center !important;
            width: 100%;
        }
        @media (prefers-color-scheme: light) {
            [data-testid="stAppViewContainer"] {
                background-color: #f9f9f9 !important;
                color: #222 !important;
            }
            .block-container {
                background: #fff !important;
                box-shadow: 0 0 10px rgba(0,0,0,0.1);
            }
            div[data-testid="stRadio"] label {
                color: #333 !important;
            }
        }
        </style>
    """, unsafe_allow_html=True)

    # ------------------------------
    # HEADER
    # ------------------------------
    st.header("📊 Dairy Dashboard")

    START_DATE = pd.Timestamp("2025-11-01")
    today = pd.Timestamp.today()
    current_month_name = today.strftime("%B %Y")

    # Filter data from 1st Nov 2025
    def filter_from_start(df):
        if "Date" in df.columns:
            df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
            return df[df["Date"] >= START_DATE]
        return df

    df_cow_log = filter_from_start(df_cow_log)
    df_expense = filter_from_start(df_expense)
    df_milk_m = filter_from_start(df_milk_m)
    df_milk_e = filter_from_start(df_milk_e)
    df_payment_received = filter_from_start(df_payment_received)
    df_investment = filter_from_start(df_investment)

    # ------------------------------
    # HELPER FUNCTION
    # ------------------------------
    def sum_numeric_columns(df, exclude_cols=None):
        if df.empty:
            return 0
        exclude_cols = exclude_cols or []
        df_numeric = df.drop(columns=[c for c in exclude_cols if c in df.columns], errors="ignore")
        return df_numeric.select_dtypes(include="number").sum().sum()

    # ------------------------------
    # LIFETIME SUMMARY
    # ------------------------------
    st.subheader("📆 Lifetime Summary")

    milk_col = next((c for c in df_cow_log.columns if "milk" in c.lower() or "दूध" in c), None)
    total_milk_produced = pd.to_numeric(df_cow_log[milk_col], errors="coerce").sum() if milk_col else 0

    total_milk_m = sum_numeric_columns(df_milk_m, exclude_cols=["Timestamp", "Date"])
    total_milk_e = sum_numeric_columns(df_milk_e, exclude_cols=["Timestamp", "Date"])
    total_milk_distributed = total_milk_m + total_milk_e
    remaining_milk = total_milk_produced - total_milk_distributed

    total_expense = pd.to_numeric(df_expense["Amount"], errors="coerce").sum() if not df_expense.empty else 0
    total_payment_received = pd.to_numeric(df_payment_received["Amount"], errors="coerce").sum() if not df_payment_received.empty else 0
    total_investment = pd.to_numeric(df_investment["Amount"], errors="coerce").sum() if not df_investment.empty else 0

    investment_bipin = df_investment.loc[df_investment["Paid To"] == "Bipin Kumar", "Amount"].sum() if "Paid To" in df_investment.columns else 0
    received_bipin = df_payment_received.loc[df_payment_received["Received By"] == "Bipin Kumar", "Amount"].sum() if "Received By" in df_payment_received.columns else 0
    expense_bipin = df_expense.loc[df_expense["Expense By"] == "Bipin Kumar", "Amount"].sum() if "Expense By" in df_expense.columns else 0
    fund_bipin = investment_bipin + received_bipin - expense_bipin

    col1, col2, col3 = st.columns(3)
    col1.metric("🥛 Total Milk Produced", f"{total_milk_produced:.2f} L")
    col2.metric("🚚 Total Milk Distributed", f"{total_milk_distributed:.2f} L")
    col3.metric("❗ Remaining / Lost Milk", f"{remaining_milk:.2f} L")

    col4, col5, col6 = st.columns(3)
    col4.metric("💰 Total Expense", f"₹{total_expense:,.2f}")
    col5.metric("🏦 Total Payment Received", f"₹{total_payment_received:,.2f}")
    col6.metric("💹 Total Investment", f"₹{total_investment:,.2f}")

    st.metric("💼 Fund Available (Bipin Kumar)", f"₹{fund_bipin:,.2f}")

    # ------------------------------
    # CURRENT MONTH SUMMARY
    # ------------------------------
    st.subheader(f"🗓️ Current Month Summary ({current_month_name})")

    df_month_expense = df_expense[df_expense["Date"].dt.month == today.month]
    df_month_milk_m = df_milk_m[df_milk_m["Date"].dt.month == today.month]
    df_month_milk_e = df_milk_e[df_milk_e["Date"].dt.month == today.month]
    df_month_cow_log = df_cow_log[df_cow_log["Date"].dt.month == today.month]
    df_month_payment = df_payment_received[df_payment_received["Date"].dt.month == today.month]

    milk_col = next((c for c in df_month_cow_log.columns if "milk" in c.lower() or "दूध" in c), None)
    milk_month = pd.to_numeric(df_month_cow_log[milk_col], errors="coerce").sum() if milk_col else 0
    milk_m_month = sum_numeric_columns(df_month_milk_m, exclude_cols=["Timestamp", "Date"])
    milk_e_month = sum_numeric_columns(df_month_milk_e, exclude_cols=["Timestamp", "Date"])
    milk_distributed_month = milk_m_month + milk_e_month
    remaining_milk_month = milk_month - milk_distributed_month
    expense_month = pd.to_numeric(df_month_expense["Amount"], errors="coerce").sum() if not df_month_expense.empty else 0
    payment_received_month = pd.to_numeric(df_month_payment["Amount"], errors="coerce").sum() if not df_month_payment.empty else 0

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("🥛 Milk Produced (This Month)", f"{milk_month:.2f} L")
    col2.metric("🚚 Milk Distributed (This Month)", f"{milk_distributed_month:.2f} L")
    col3.metric("❗ Remaining Milk (This Month)", f"{remaining_milk_month:.2f} L")
    col4.metric("💰 Expense (This Month)", f"₹{expense_month:,.2f}")
    col5.metric("🏦 Payment Received (This Month)", f"₹{payment_received_month:,.2f}")

    # ------------------------------
    # INTERACTIVE GRAPH (Plotly)
    # ------------------------------
    st.divider()
    st.subheader("📈 Milk Produced vs Delivered Over Time")

    st.markdown('<div class="radio-center">', unsafe_allow_html=True)
    period = st.radio(
        "Select Duration:",
        ["1 Week", "1 Month", "3 Months", "6 Months", "1 Year", "All"],
        horizontal=True,
    )
    st.markdown('</div>', unsafe_allow_html=True)

    df_cow_log["Date"] = pd.to_datetime(df_cow_log["Date"], errors="coerce")
    df_milk_m["Date"] = pd.to_datetime(df_milk_m["Date"], errors="coerce")
    df_milk_e["Date"] = pd.to_datetime(df_milk_e["Date"], errors="coerce")

    end_date = today
    if period == "1 Week":
        start_date = end_date - pd.Timedelta(weeks=1)
    elif period == "1 Month":
        start_date = end_date - pd.Timedelta(days=30)
    elif period == "3 Months":
        start_date = end_date - pd.Timedelta(days=90)
    elif period == "6 Months":
        start_date = end_date - pd.Timedelta(days=180)
    elif period == "1 Year":
        start_date = end_date - pd.Timedelta(days=365)
    else:
        start_date = START_DATE

    df_filtered = df_cow_log[df_cow_log["Date"].between(start_date, end_date)]
    milk_daily = (
        df_filtered.groupby("Date")[milk_col].sum().reset_index()
        if milk_col and not df_filtered.empty else pd.DataFrame()
    )

    def get_daily_distribution(df):
        if df.empty:
            return pd.DataFrame()
        df["Date"] = pd.to_datetime(df["Date"])
        numeric_cols = [c for c in df.columns if c not in ["Timestamp", "Date"]]
        df_daily = df[numeric_cols].apply(pd.to_numeric, errors="coerce")
        return pd.DataFrame({"Date": df["Date"], "Delivered": df_daily.sum(axis=1)})

    df_m_m = get_daily_distribution(df_milk_m)
    df_m_e = get_daily_distribution(df_milk_e)
    df_delivered = pd.concat([df_m_m, df_m_e]).groupby("Date")["Delivered"].sum().reset_index()

    if not milk_daily.empty and not df_delivered.empty:
        df_chart = pd.merge(milk_daily, df_delivered, on="Date", how="outer").fillna(0)
        fig = px.line(
            df_chart,
            x="Date",
            y=["Milking -दूध", "Delivered"],
            labels={"value": "Milk (L)", "Date": "Date"},
            title="Milk Produced vs Delivered",
            template="plotly_dark",
            markers=True,
        )
        fig.update_layout(
            hovermode="x unified",
            legend_title_text="Legend",
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data available for the selected period.")



# ----------------------------
# MILKING & FEEDING PAGE
# ----------------------------
elif page == "Milking & Feeding":
    st.title("🐄 Milking & Feeding Analysis")

    # --- Load data ---
    df = load_csv(COW_LOG_CSV_URL, drop_cols=["Timestamp"])
    df_morning = load_csv(MILK_DIS_M_CSV_URL, drop_cols=["Timestamp"])
    df_evening = load_csv(MILK_DIS_E_CSV_URL, drop_cols=["Timestamp"])

    # --- Date setup ---
    start_date = pd.Timestamp("2025-11-01")
    now = pd.Timestamp.now()
    this_month = now.month
    this_year = now.year

    # --- Clean and filter helper ---
    def clean_and_filter(df):
        if df.empty or "Date" not in df.columns:
            return df
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        df = df[df["Date"] >= start_date]
        df["Date"] = df["Date"].dt.strftime("%d-%m-%Y")
        return df

    df = clean_and_filter(df)
    df_morning = clean_and_filter(df_morning)
    df_evening = clean_and_filter(df_evening)

    # --- Detect milk column dynamically ---
    milk_col = None
    for c in df.columns:
        if "milk" in c.lower() or "दूध" in c:
            milk_col = c
            break

    # --- Ensure numeric ---
    if not df.empty and milk_col:
        df[milk_col] = pd.to_numeric(df[milk_col], errors="coerce")

    # --- Total milk produced ---
    total_milk_produced = df[milk_col].sum() if not df.empty and milk_col else 0

    # --- Total milk this month ---
    total_milk_month = 0
    if not df.empty and milk_col:
        df["Date_dt"] = pd.to_datetime(df["Date"], format="%d-%m-%Y", errors="coerce")
        df_this_month = df[
            (df["Date_dt"].dt.month == this_month) & (df["Date_dt"].dt.year == this_year)
        ]
        if not df_this_month.empty:
            total_milk_month = df_this_month[milk_col].sum()

    # --- Cow-wise total ---
    cow_wise = pd.DataFrame()
    if not df.empty and "CowID" in df.columns and milk_col:
        cow_wise = (
            df.groupby("CowID")[milk_col]
            .sum()
            .reset_index()
            .rename(columns={milk_col: "Total Milk (L)"})
            .sort_values("Total Milk (L)", ascending=False)
        )

    # --- Total Milk Distributed ---
    def total_milk_distributed(df):
        if df.empty:
            return 0
        numeric_cols = [c for c in df.columns if c not in ["Timestamp", "Date"]]
        df_numeric = df[numeric_cols].apply(pd.to_numeric, errors="coerce")
        return df_numeric.sum().sum()

    total_distributed_morning = total_milk_distributed(df_morning)
    total_distributed_evening = total_milk_distributed(df_evening)
    total_distributed = total_distributed_morning + total_distributed_evening

    # --- KPIs ---
    st.subheader("📊 Key Metrics (From 1 Nov 2025)")
    col1, col2, col3 = st.columns(3)
    col1.metric("🥛 Total Milk Produced", f"{total_milk_produced:.2f} L")
    col2.metric("📅 Milk Produced This Month", f"{total_milk_month:.2f} L")
    col3.metric("🚚 Total Milk Delivered", f"{total_distributed:.2f} L")

    # --- Cow-wise production ---
    st.divider()
    st.subheader("🐮 Cow-wise Milk Production (From 1 Nov 2025)")
    if not cow_wise.empty:
        st.dataframe(cow_wise, use_container_width=True)
    else:
        st.info("No cow-wise milking data available yet.")

    # --- Daily trend ---
    st.divider()
    st.subheader("📅 Daily Milk Production Trend")
    if not df.empty and milk_col:
        df_daily = df.copy()
        df_daily["Date_dt"] = pd.to_datetime(df_daily["Date"], format="%d-%m-%Y", errors="coerce")
        daily_summary = (
            df_daily.groupby("Date_dt")[milk_col].sum().reset_index().sort_values("Date_dt")
        )
        st.line_chart(daily_summary.set_index("Date_dt"))
    else:
        st.info("No daily milking data to display.")

    # --- Raw data ---
    st.divider()
    st.subheader("📋 Raw Milking & Feeding Data (From 1 Nov 2025)")
    if not df.empty:
        df_display = df.sort_values(by="Date", ascending=False)
        st.dataframe(df_display, use_container_width=True)
    else:
        st.info("No milking & feeding data available after 1 Nov 2025.")


# ----------------------------
# MILK DISTRIBUTION PAGE
# ----------------------------
elif page == "Milk Distribution":
    st.title("🥛 Milk Distribution")

    # --- Load data ---
    df_morning = load_csv(MILK_DIS_M_CSV_URL, drop_cols=["Timestamp"])
    df_evening = load_csv(MILK_DIS_E_CSV_URL, drop_cols=["Timestamp"])
    df_cow_log = load_csv(COW_LOG_CSV_URL, drop_cols=["Timestamp"])

    # --- Date filtering: only include records from 1 Nov 2025 onward ---
    start_date = pd.Timestamp("2025-11-01")

    def clean_and_filter(df):
        if df.empty or "Date" not in df.columns:
            return df
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        df = df[df["Date"] >= start_date]  # Filter only from 1 Nov 2025
        df["Date"] = df["Date"].dt.strftime("%d-%m-%Y")  # Format date
        return df

    df_morning = clean_and_filter(df_morning)
    df_evening = clean_and_filter(df_evening)

    # --- Total milk distributed (sum numeric columns except date) ---
    def total_milk_distributed(df):
        if df.empty:
            return 0
        numeric_cols = [c for c in df.columns if c not in ["Timestamp", "Date"]]
        df_numeric = df[numeric_cols].apply(pd.to_numeric, errors="coerce")
        return df_numeric.sum().sum()

    total_morning = total_milk_distributed(df_morning)
    total_evening = total_milk_distributed(df_evening)
    total_distributed = total_morning + total_evening

    # --- Monthly totals ---
    this_month = pd.Timestamp.now().month
    this_year = pd.Timestamp.now().year

    def monthly_distribution(df):
        if df.empty or "Date" not in df.columns:
            return 0
        df["Date"] = pd.to_datetime(df["Date"], format="%d-%m-%Y", errors="coerce")
        df_this_month = df[
            (df["Date"].dt.month == this_month) & (df["Date"].dt.year == this_year)
        ]
        return total_milk_distributed(df_this_month)

    monthly_morning = monthly_distribution(df_morning)
    monthly_evening = monthly_distribution(df_evening)
    monthly_distributed = monthly_morning + monthly_evening

    # --- Total milk produced this month from cow log (filter from 1 Nov 2025) ---
    total_milk_produced_month = 0
    if not df_cow_log.empty:
        df_cow_log.columns = [c.strip().lower() for c in df_cow_log.columns]
        if "date" in df_cow_log.columns and "milking -दूध" in df_cow_log.columns:
            df_cow_log["date"] = pd.to_datetime(df_cow_log["date"], errors="coerce")
            df_cow_log = df_cow_log[df_cow_log["date"] >= start_date]  # Filter Nov 1 onward
            df_cow_log["month"] = df_cow_log["date"].dt.month
            df_cow_log["year"] = df_cow_log["date"].dt.year
            df_month = df_cow_log[
                (df_cow_log["month"] == this_month) & (df_cow_log["year"] == this_year)
            ]
            total_milk_produced_month = pd.to_numeric(
                df_month["milking -दूध"], errors="coerce"
            ).sum()

    remaining_milk = total_milk_produced_month - monthly_distributed

    # --- KPI Metrics ---
    col1, col2, col3 = st.columns(3)
    col1.metric("🥛 Total Milk Distributed (from 1 Nov 2025)", f"{total_distributed:.2f} L")
    col2.metric("📅 This Month's Distribution", f"{monthly_distributed:.2f} L")
    col3.metric("🧾 Remaining Milk (This Month)", f"{remaining_milk:.2f} L")

    st.divider()

    # --- Morning Distribution Table ---
    st.subheader("🌅 Morning Distribution")
    if not df_morning.empty:
        df_morning_display = df_morning.sort_values("Date", ascending=False)
        st.dataframe(df_morning_display, use_container_width=True)
    else:
        st.info("No morning distribution data available after 1 Nov 2025.")

    # --- Evening Distribution Table ---
    st.subheader("🌇 Evening Distribution")
    if not df_evening.empty:
        df_evening_display = df_evening.sort_values("Date", ascending=False)
        st.dataframe(df_evening_display, use_container_width=True)
    else:
        st.info("No evening distribution data available after 1 Nov 2025.")

    # --- Trend Chart ---
    st.divider()
    st.subheader("📈 Daily Milk Distribution Trend (from 1 Nov 2025)")

    if not df_morning.empty or not df_evening.empty:
        df_morning_chart = df_morning.copy()
        df_evening_chart = df_evening.copy()

        for df_temp in [df_morning_chart, df_evening_chart]:
            df_temp["Date"] = pd.to_datetime(df_temp["Date"], format="%d-%m-%Y", errors="coerce")
            df_temp["Total"] = df_temp.select_dtypes(include=["number"]).sum(axis=1)

        df_chart = pd.concat([
            df_morning_chart[["Date", "Total"]],
            df_evening_chart[["Date", "Total"]],
        ])
        df_chart = df_chart.groupby("Date")["Total"].sum().reset_index().sort_values("Date")

        st.line_chart(df_chart.set_index("Date"))
    else:
        st.info("No distribution data available to plot.")


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
