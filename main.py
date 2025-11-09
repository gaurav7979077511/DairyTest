import streamlit as st
import pandas as pd

# ============================================================
# PAGE CONFIGURATION
# ============================================================
st.set_page_config(page_title="Dairy Farm Management", layout="wide")

# ============================================================
# GOOGLE SHEET IDS (from Streamlit Secrets)
# ============================================================
INVESTMENT_SHEET_ID = st.secrets["sheets"]["INVESTMENT_SHEET_ID"]
MILK_DIS_M_SHEET_ID = st.secrets["sheets"]["MILK_DIS_M_SHEET_ID"]
MILK_DIS_E_SHEET_ID = st.secrets["sheets"]["MILK_DIS_E_SHEET_ID"]
EXPENSE_SHEET_ID = st.secrets["sheets"]["EXPENSE_SHEET_ID"]
COW_LOG_SHEET_ID = st.secrets["sheets"]["COW_LOG_SHEET_ID"]
PAYMENT_SHEET_ID = st.secrets["sheets"]["PAYMENT_SHEET_ID"]

# ============================================================
# GOOGLE SHEET CSV EXPORT LINKS
# ============================================================
INVESTMENT_CSV_URL = f"https://docs.google.com/spreadsheets/d/{INVESTMENT_SHEET_ID}/gviz/tq?tqx=out:csv&sheet=investment"
MILK_DIS_M_CSV_URL = f"https://docs.google.com/spreadsheets/d/{MILK_DIS_M_SHEET_ID}/gviz/tq?tqx=out:csv&sheet=morning"
MILK_DIS_E_CSV_URL = f"https://docs.google.com/spreadsheets/d/{MILK_DIS_E_SHEET_ID}/gviz/tq?tqx=out:csv&sheet=evening"
EXPENSE_CSV_URL = f"https://docs.google.com/spreadsheets/d/{EXPENSE_SHEET_ID}/gviz/tq?tqx=out:csv&sheet=expense"
COW_LOG_CSV_URL = f"https://docs.google.com/spreadsheets/d/{COW_LOG_SHEET_ID}/gviz/tq?tqx=out:csv&sheet=dailylog"
PAYMENT_CSV_URL = f"https://docs.google.com/spreadsheets/d/{PAYMENT_SHEET_ID}/gviz/tq?tqx=out:csv&sheet=payment"

# ============================================================
# UTILITY FUNCTIONS
# ============================================================
@st.cache_data(ttl=600)
def load_csv(url, drop_cols=None):
    """Load a CSV from Google Sheets"""
    try:
        df = pd.read_csv(url)
        if drop_cols:
            df = df.drop(columns=[col for col in drop_cols if col in df.columns])
        return df
    except Exception as e:
        st.error(f"❌ Failed to load data from Google Sheet: {e}")
        return pd.DataFrame()


def sum_numeric_columns(df, exclude_cols=None):
    """Sum all numeric columns except excluded ones"""
    if df.empty:
        return 0
    if exclude_cols is None:
        exclude_cols = []
    numeric_cols = [col for col in df.columns if col not in exclude_cols]
    df_numeric = df[numeric_cols].apply(pd.to_numeric, errors="coerce")
    return df_numeric.sum().sum()

# ============================================================
# SIDEBAR NAVIGATION
# ============================================================
st.sidebar.header("Navigation")
page = st.sidebar.radio(
    "Go to",
    [
        "🏠 Dashboard",
        "Milking & Feeding",
        "Milk Distribution",
        "Expense",
        "Payments",
        "Investments",
    ],
)

# ============================================================
# 🏠 DASHBOARD PAGE
# ============================================================
if page == "🏠 Dashboard":

    # -------------------- Custom Dark Mode CSS --------------------
    st.markdown(
        """
        <style>
        :root {
            --bg-color: #0e1117;
            --card-bg: #1a1d23;
            --text-color: #f0f2f6;
            --accent: #00FFFF;
            --border-color: #00FFFF44;
            --shadow-color: #00FFFF22;
        }
        @media (prefers-color-scheme: light) {
            :root {
                --bg-color: #f9f9f9;
                --card-bg: #ffffff;
                --text-color: #000000;
                --accent: #0077ff;
                --border-color: #0077ff33;
                --shadow-color: #0077ff11;
            }
        }
        .main { background-color: var(--bg-color); color: var(--text-color); }
        div[data-testid="stMetric"] {
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 15px;
            padding: 15px;
            box-shadow: 0 0 8px var(--shadow-color);
            text-align: center;
        }
        h1, h2, h3 { color: var(--accent); }
        hr { border: 1px solid var(--border-color); }
        label, .stRadio { color: var(--text-color) !important; }
        @media (max-width: 768px) {
            div[data-testid="stMetric"] { padding: 10px; font-size: 0.85rem; }
            h1, h2, h3 { font-size: 1rem; }
        }
        .radio-center { display: flex; justify-content: center; margin-top: 10px; margin-bottom: 25px; }
        div[data-testid="stRadio"] > div { justify-content: center !important; }
        div[data-testid="stRadio"] label { color: var(--text-color) !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.header("🐄 Dairy Farm Dashboard")

    # -------------------- Load Data --------------------
    START_DATE = pd.Timestamp("2025-11-01")
    df_cow_log = load_csv(COW_LOG_CSV_URL, drop_cols=["Timestamp"])
    df_expense = load_csv(EXPENSE_CSV_URL, drop_cols=["Timestamp"])
    df_milk_m = load_csv(MILK_DIS_M_CSV_URL, drop_cols=["Timestamp"])
    df_milk_e = load_csv(MILK_DIS_E_CSV_URL, drop_cols=["Timestamp"])
    df_payment_received = load_csv(PAYMENT_CSV_URL, drop_cols=["Timestamp"])
    df_investment = load_csv(INVESTMENT_CSV_URL, drop_cols=["Timestamp"])

    # -------------------- Filter from 1 Nov 2025 --------------------
    for df in [df_cow_log, df_expense, df_milk_m, df_milk_e, df_payment_received, df_investment]:
        if "Date" in df.columns:
            df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
            df.dropna(subset=["Date"], inplace=True)
            df = df[df["Date"] >= START_DATE]

    # -------------------- Lifetime Summary --------------------
    st.subheader("📊 Overall Summary")

    milk_col = next((c for c in df_cow_log.columns if "milk" in c.lower() or "दूध" in c), None)
    total_milk_produced = pd.to_numeric(df_cow_log[milk_col], errors="coerce").sum() if milk_col else 0

    total_milk_m = sum_numeric_columns(df_milk_m, exclude_cols=["Timestamp", "Date"])
    total_milk_e = sum_numeric_columns(df_milk_e, exclude_cols=["Timestamp", "Date"])
    total_milk_distributed = total_milk_m + total_milk_e
    remaining_milk = total_milk_produced - total_milk_distributed

    total_expense = pd.to_numeric(df_expense["Amount"], errors="coerce").sum() if not df_expense.empty else 0
    total_payment_received = pd.to_numeric(df_payment_received["Amount"], errors="coerce").sum() if not df_payment_received.empty else 0
    total_investment = pd.to_numeric(df_investment["Amount"], errors="coerce").sum() if not df_investment.empty else 0

    investment_bipin = (
        df_investment.loc[df_investment["Paid To"] == "Bipin Kumar", "Amount"].sum()
        if "Paid To" in df_investment.columns
        else 0
    )
    received_bipin = (
        df_payment_received.loc[df_payment_received["Received By"] == "Bipin Kumar", "Amount"].sum()
        if "Received By" in df_payment_received.columns
        else 0
    )
    expense_bipin = (
        df_expense.loc[df_expense["Expense By"] == "Bipin Kumar", "Amount"].sum()
        if "Expense By" in df_expense.columns
        else 0
    )
    fund_bipin = investment_bipin + received_bipin - expense_bipin

    # -------------------- Metrics --------------------
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🥛 Total Milk Produced", f"{total_milk_produced:.2f} L")
    c2.metric("🚚 Total Milk Distributed", f"{total_milk_distributed:.2f} L")
    c3.metric("❗ Remaining / Lost Milk", f"{remaining_milk:.2f} L")
    c4.metric("💸 Total Expense", f"₹{total_expense:,.2f}")

    c5, c6, c7 = st.columns(3)
    c5.metric("💰 Total Payment Received", f"₹{total_payment_received:,.2f}")
    c6.metric("📈 Total Investment", f"₹{total_investment:,.2f}")
    c7.metric("🏦 Fund (Bipin Kumar)", f"₹{fund_bipin:,.2f}")

    st.markdown("<hr/>", unsafe_allow_html=True)

    # -------------------- Current Month Summary --------------------
    today = pd.Timestamp.today()
    current_month_name = today.strftime("%B %Y")
    st.subheader(f"📅 Current Month Summary ({current_month_name})")

    def filter_month(df):
        if df.empty or "Date" not in df.columns:
            return df
        return df[df["Date"].dt.month == today.month]

    df_month_expense = filter_month(df_expense)
    df_month_milk_m = filter_month(df_milk_m)
    df_month_milk_e = filter_month(df_milk_e)
    df_month_cow_log = filter_month(df_cow_log)
    df_month_payment = filter_month(df_payment_received)

    milk_col = next((c for c in df_month_cow_log.columns if "milk" in c.lower() or "दूध" in c), None)
    milk_month = pd.to_numeric(df_month_cow_log[milk_col], errors="coerce").sum() if milk_col else 0
    milk_m_month = sum_numeric_columns(df_month_milk_m, exclude_cols=["Timestamp", "Date"])
    milk_e_month = sum_numeric_columns(df_month_milk_e, exclude_cols=["Timestamp", "Date"])
    milk_distributed_month = milk_m_month + milk_e_month
    remaining_milk_month = milk_month - milk_distributed_month

    expense_month = pd.to_numeric(df_month_expense["Amount"], errors="coerce").sum() if not df_month_expense.empty else 0
    payment_month = pd.to_numeric(df_month_payment["Amount"], errors="coerce").sum() if not df_month_payment.empty else 0

    cm1, cm2, cm3, cm4, cm5 = st.columns(5)
    cm1.metric("🥛 Milk Produced (This Month)", f"{milk_month:.2f} L")
    cm2.metric("🚚 Milk Distributed (This Month)", f"{milk_distributed_month:.2f} L")
    cm3.metric("❗ Remaining Milk (This Month)", f"{remaining_milk_month:.2f} L")
    cm4.metric("💸 Expense (This Month)", f"₹{expense_month:,.2f}")
    cm5.metric("💰 Payment Received (This Month)", f"₹{payment_month:,.2f}")

    st.markdown("<hr/>", unsafe_allow_html=True)

    # -------------------- Milk Production vs Delivery Graph --------------------
    # -------------------- Milk Production vs Delivery Graph --------------------
    st.subheader("📈 Milk Production vs Delivery Trend")
    
    # --- Centered Radio Button for Date Range
    col1, col2, col3 = st.columns([1, 3, 1])  # Center alignment
    with col2:
        range_option = st.radio(
            "",
            ["1 Week", "1 Month", "3 Months", "6 Months", "1 Year", "3 Years", "5 Years", "Max"],
            horizontal=True,
            index=1,  # Default to "3 Months"
        )
    
    # --- Determine date range based on selection
    today = pd.Timestamp.today()
    date_limit = {
        "1 Week": today - pd.Timedelta(weeks=1),
        "1 Month": today - pd.DateOffset(months=1),
        "3 Months": today - pd.DateOffset(months=3),
        "6 Months": today - pd.DateOffset(months=6),
        "1 Year": today - pd.DateOffset(years=1),
        "3 Years": today - pd.DateOffset(years=3),
        "5 Years": today - pd.DateOffset(years=5),
        "Max": START_DATE,
    }[range_option]
    
    # --- Prepare production data
    if not df_cow_log.empty and milk_col:
        df_cow_log["Date"] = pd.to_datetime(df_cow_log["Date"], errors="coerce")
        df_cow_log = df_cow_log[df_cow_log["Date"] >= date_limit]
        daily_prod = df_cow_log.groupby("Date")[milk_col].sum().reset_index()
    else:
        daily_prod = pd.DataFrame(columns=["Date", "Produced"])
    
    # --- Combine morning & evening distribution
    def combine_distribution(df1, df2):
        df_all = pd.concat([df1, df2])
        df_all["Date"] = pd.to_datetime(df_all["Date"], errors="coerce")
        df_all["Total"] = df_all.select_dtypes(include="number").sum(axis=1)
        return df_all.groupby("Date")["Total"].sum().reset_index()
    
    df_delivery = combine_distribution(df_milk_m, df_milk_e)
    df_delivery = df_delivery[df_delivery["Date"] >= date_limit]
    
    # --- Display line chart
    if not daily_prod.empty and not df_delivery.empty:
        chart_df = pd.merge(daily_prod, df_delivery, on="Date", how="outer").fillna(0)
        chart_df = chart_df.rename(columns={milk_col: "Produced", "Total": "Delivered"})
        st.line_chart(chart_df.set_index("Date"))
    else:
        st.info("No sufficient data for chart.")


# ============================================================
# 🐄 MILKING & FEEDING PAGE
# ============================================================
elif page == "Milking & Feeding":
    st.title("🐄 Milking & Feeding Data")

    # -------------------- Load Data --------------------
    df = load_csv(COW_LOG_CSV_URL, drop_cols=["Timestamp"])
    df_morning = load_csv(MILK_DIS_M_CSV_URL, drop_cols=["Timestamp"])
    df_evening = load_csv(MILK_DIS_E_CSV_URL, drop_cols=["Timestamp"])

    # -------------------- Date setup --------------------
    start_date = pd.Timestamp("2025-11-01")
    now = pd.Timestamp.now()
    this_month = now.month
    this_year = now.year

    # -------------------- Helper Function --------------------
    def clean_dates(df):
        if df.empty or "Date" not in df.columns:
            return df
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce", dayfirst=True)
        df.dropna(subset=["Date"], inplace=True)
        df = df[df["Date"] >= start_date]
        return df

    df = clean_dates(df)
    df_morning = clean_dates(df_morning)
    df_evening = clean_dates(df_evening)

    # -------------------- Detect Milk Column --------------------
    milk_col = next((c for c in df.columns if "milk" in c.lower() or "दूध" in c), None)
    if not df.empty and milk_col:
        df[milk_col] = pd.to_numeric(df[milk_col], errors="coerce")

    # -------------------- Total Milk Produced --------------------
    total_milk_produced = df[milk_col].sum() if not df.empty and milk_col else 0

    # -------------------- Total Milk Delivered (same logic as Dashboard) --------------------
    total_milk_m = sum_numeric_columns(df_morning, exclude_cols=["Timestamp", "Date"])
    total_milk_e = sum_numeric_columns(df_evening, exclude_cols=["Timestamp", "Date"])
    total_distributed = total_milk_m + total_milk_e

    # -------------------- This Month’s Milk --------------------
    total_milk_month = 0
    total_distributed_month = 0

    if not df.empty and milk_col:
        df_this_month = df[
            (df["Date"].dt.month == this_month) & (df["Date"].dt.year == this_year)
        ]
        total_milk_month = df_this_month[milk_col].sum() if not df_this_month.empty else 0

    # Same month filtering logic as Dashboard
    def filter_month(df):
        if df.empty or "Date" not in df.columns:
            return df
        return df[(df["Date"].dt.month == this_month) & (df["Date"].dt.year == this_year)]

    df_morning_month = filter_month(df_morning)
    df_evening_month = filter_month(df_evening)
    milk_m_month = sum_numeric_columns(df_morning_month, exclude_cols=["Timestamp", "Date"])
    milk_e_month = sum_numeric_columns(df_evening_month, exclude_cols=["Timestamp", "Date"])
    total_distributed_month = milk_m_month + milk_e_month

    # -------------------- Overall Metrics --------------------
    st.subheader("📊 Overall Metrics (From 1 Nov 2025)")
    col1, col2 = st.columns(2)
    col1.metric("🥛 Total Milk Produced", f"{total_milk_produced:.2f} L")
    col2.metric("🚚 Total Milk Delivered", f"{total_distributed:.2f} L")

    st.divider()

    # -------------------- Monthly Summary --------------------
    st.subheader(f"📅 Milk Summary - {now.strftime('%B %Y')}")
    col3, col4 = st.columns(2)
    col3.metric("🥛 Milk Produced This Month", f"{total_milk_month:.2f} L")
    col4.metric("🚚 Milk Delivered This Month", f"{total_distributed_month:.2f} L")

    st.divider()

    # -------------------- Raw Data --------------------
    st.subheader("🗃 Raw Data")

    st.markdown("#### Milking & Feeding Log")
    if not df.empty and "Date" in df.columns:
        df_sorted = df.sort_values(by="Date", ascending=False)
        st.dataframe(df_sorted, use_container_width=True)
    else:
        st.info("No milking or feeding data available.")


# ============================================================
# 🚚 MILK DISTRIBUTION PAGE
# ============================================================
elif page == "Milk Distribution":
    st.title("🚚 Milk Distribution Summary")
    df_morning = load_csv(MILK_DIS_M_CSV_URL)
    df_evening = load_csv(MILK_DIS_E_CSV_URL)

    st.subheader("🌅 Morning Distribution")
    if not df_morning.empty:
        st.dataframe(df_morning, use_container_width=True)
        st.metric(
            "Total Morning Milk Distributed",
            f"{sum_numeric_columns(df_morning, ['Timestamp', 'Date']):.2f} L",
        )
    else:
        st.warning("No morning data available")

    st.divider()

    st.subheader("🌇 Evening Distribution")
    if not df_evening.empty:
        st.dataframe(df_evening, use_container_width=True)
        st.metric(
            "Total Evening Milk Distributed",
            f"{sum_numeric_columns(df_evening, ['Timestamp', 'Date']):.2f} L",
        )
    else:
        st.warning("No evening data available")

# ============================================================
# 💸 EXPENSE PAGE
# ============================================================
elif page == "Expense":
    st.title("💸 Expense Tracker")
    df_expense = load_csv(EXPENSE_CSV_URL)
    if df_expense.empty:
        st.warning("No expense data available.")
    else:
        df_expense["Amount"] = pd.to_numeric(df_expense["Amount"], errors="coerce")
        st.dataframe(df_expense, use_container_width=True)
        st.metric("Total Expense", f"₹{df_expense['Amount'].sum():,.2f}")

# ============================================================
# 💰 PAYMENTS PAGE
# ============================================================
elif page == "Payments":
    st.title("💰 Payments Received")
    df_payment = load_csv(PAYMENT_CSV_URL)
    if df_payment.empty:
        st.warning("No payment data available.")
    else:
        df_payment["Amount"] = pd.to_numeric(df_payment["Amount"], errors="coerce")
        st.dataframe(df_payment, use_container_width=True)
        st.metric("Total Payment Received", f"₹{df_payment['Amount'].sum():,.2f}")

# ============================================================
# 💼 INVESTMENTS PAGE
# ============================================================
elif page == "Investments":
    st.title("💼 Investment Summary")
    df_investment = load_csv(INVESTMENT_CSV_URL)
    if df_investment.empty:
        st.warning("No investment data available.")
    else:
        df_investment["Amount"] = pd.to_numeric(df_investment["Amount"], errors="coerce")
        st.dataframe(df_investment, use_container_width=True)
        st.metric("Total Investment", f"₹{df_investment['Amount'].sum():,.2f}")
