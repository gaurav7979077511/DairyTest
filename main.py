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

# ----------------------------
# MILKING & FEEDING PAGE
# ----------------------------
elif page == "Milking & Feeding":
    st.title("🐄 Milking & Feeding Analysis")

    # Add Expense Button
    col1, col2 = st.columns([6, 1])
    with col2:
        st.markdown(
            f'<a href="https://forms.gle/4ywNpoYLr7LFQtxe8" target="_blank">'
            f'<button style="background-color:#4CAF50; color:white; padding:8px 16px; font-size:14px; border:none; border-radius:5px;">➕ Add Expenses</button>'
            f'</a>',
            unsafe_allow_html=True
        )
    
        # ─────────────────────────────────────────────────────

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
