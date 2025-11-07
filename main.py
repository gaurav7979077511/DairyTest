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
# CONSTANTS
# ----------------------------
START_DATE = pd.Timestamp("2025-11-01")  # only keep data from 1 Nov 2025 onward

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

# ----------------------------
# HELPER FUNCTIONS
# ----------------------------
def sum_numeric_columns(df, exclude_cols=None):
    """Sum all numeric columns except the excluded ones (used for milk totals)."""
    if df is None or df.empty:
        return 0
    if exclude_cols is None:
        exclude_cols = []
    numeric_cols = [col for col in df.columns if col not in exclude_cols]
    df_numeric = df[numeric_cols].apply(pd.to_numeric, errors="coerce")
    return df_numeric.sum().sum()

def safe_parse_date_col(df, col_name="Date"):
    """Return a datetime series if the column exists; else Series of NaT."""
    if df is None or df.empty or col_name not in df.columns:
        return pd.Series(pd.NaT, index=df.index if isinstance(df, pd.DataFrame) else [])
    return pd.to_datetime(df[col_name], errors="coerce")

def detect_milk_column(df):
    """Try to find a column name in df that likely contains milk liters."""
    if df is None or df.empty:
        return None
    for c in df.columns:
        if "milk" in c.lower() or "दूध" in c:
            return c
    return None

def filter_from_start_date(df, date_col="Date"):
    """Filter dataframe to only rows where date_col >= START_DATE.
       Convert the date_col back to string dd-mm-yyyy for display (but keep original dt in a helper)."""
    if df is None or df.empty or date_col not in df.columns:
        return df
    df = df.copy()
    df[date_col + "_dt"] = pd.to_datetime(df[date_col], errors="coerce")
    df = df[df[date_col + "_dt"] >= START_DATE]
    df[date_col] = df[date_col + "_dt"].dt.strftime("%d-%m-%Y")
    return df

# ----------------------------
# SIDEBAR NAVIGATION
# ----------------------------
st.sidebar.header("Navigation")
page = st.sidebar.radio(
    "Go to",
    ["🏠 Dashboard", "Milking & Feeding", "Milk Distribution", "Expense", "Payments", "Investments"]
)

# ----------------------------
# DASHBOARD PAGE
# ----------------------------
if page == "🏠 Dashboard":
    st.title("🐄 Dairy Farm Dashboard (from 1 Nov 2025)")
    st.caption("Overview of farm performance: finances, milk production & distribution.")

    # Load raw sheets
    df_expense = load_csv(EXPENSE_CSV_URL, drop_cols=["Timestamp"])
    df_invest = load_csv(INVESTMENT_CSV_URL, drop_cols=["Timestamp"])
    df_payment = load_csv(PAYMENT_CSV_URL, drop_cols=["Timestamp"])
    df_milk_m = load_csv(MILK_DIS_M_CSV_URL, drop_cols=["Timestamp"])
    df_milk_e = load_csv(MILK_DIS_E_CSV_URL, drop_cols=["Timestamp"])
    df_cow_log = load_csv(COW_LOG_CSV_URL, drop_cols=["Timestamp"])

    # Filter all relevant datasets from START_DATE
    df_expense = filter_from_start_date(df_expense, "Date") if not df_expense.empty else df_expense
    df_invest = filter_from_start_date(df_invest, "Date") if not df_invest.empty else df_invest
    df_payment = filter_from_start_date(df_payment, "Date") if not df_payment.empty else df_payment
    df_milk_m = filter_from_start_date(df_milk_m, "Date") if not df_milk_m.empty else df_milk_m
    df_milk_e = filter_from_start_date(df_milk_e, "Date") if not df_milk_e.empty else df_milk_e
    df_cow_log = filter_from_start_date(df_cow_log, "Date") if not df_cow_log.empty else df_cow_log

    # --- Financial totals (lifetime since START_DATE) ---
    total_expense = df_expense["Amount"].sum() if "Amount" in df_expense.columns else 0
    total_invest = df_invest["Amount"].sum() if "Amount" in df_invest.columns else 0
    total_payment = df_payment["Amount"].sum() if "Amount" in df_payment.columns else 0

    # --- Distribution totals (lifetime since START_DATE) ---
    total_milk_m = sum_numeric_columns(df_milk_m, exclude_cols=["Timestamp", "Date"])
    total_milk_e = sum_numeric_columns(df_milk_e, exclude_cols=["Timestamp", "Date"])
    total_distributed = total_milk_m + total_milk_e

    # --- Production totals (lifetime since START_DATE) ---
    milk_col = detect_milk_column(df_cow_log)
    if milk_col and milk_col in df_cow_log.columns:
        df_cow_log[milk_col] = pd.to_numeric(df_cow_log[milk_col], errors="coerce")
        total_produced = df_cow_log[milk_col].sum()
    else:
        total_produced = 0

    # --- Fund at Bipin Kumar (lifetime since START_DATE) ---
    total_invest_bipin = df_invest[df_invest.get("Paid To","").str.contains("Bipin Kumar", case=False, na=False)]["Amount"].sum() if "Paid To" in df_invest.columns and "Amount" in df_invest.columns else 0
    total_payment_bipin = df_payment[df_payment.get("Received By","").str.contains("Bipin Kumar", case=False, na=False)]["Amount"].sum() if "Received By" in df_payment.columns and "Amount" in df_payment.columns else 0
    total_expense_bipin = df_expense[df_expense.get("Expense By","").str.contains("Bipin Kumar", case=False, na=False)]["Amount"].sum() if "Expense By" in df_expense.columns and "Amount" in df_expense.columns else 0
    fund_bipin = total_invest_bipin + total_payment_bipin - total_expense_bipin

    # ----------------------------
    # LIFETIME SUMMARY (since START_DATE)
    # ----------------------------
    st.markdown("### 📅 Lifetime Summary (from 01-Nov-2025)")
    fcol1, fcol2, fcol3, fcol4 = st.columns(4)
    fcol1.metric("💸 Total Expenses", f"₹{total_expense:,.2f}")
    fcol2.metric("📈 Total Investment", f"₹{total_invest:,.2f}")
    fcol3.metric("💰 Total Payments", f"₹{total_payment:,.2f}")
    fcol4.metric("💼 Fund (Bipin Kumar)", f"₹{fund_bipin:,.2f}")

    st.markdown("---")
    mcol1, mcol2, mcol3, mcol4 = st.columns(4)
    mcol1.metric("🥛 Total Milk Produced", f"{total_produced:.2f} L")
    mcol2.metric("🚚 Total Milk Distributed", f"{total_distributed:.2f} L")
    remaining_alltime = total_produced - total_distributed
    mcol3.metric("❗ Remaining / Lost Milk", f"{remaining_alltime:.2f} L")
    mcol4.metric("🗓️ From Date", "01-11-2025")

    # --- Production vs Distribution chart ---
    st.markdown("#### 📊 Production vs Distribution (Lifetime)")
    chart_df = pd.DataFrame({
        "Category": ["Produced", "Distributed", "Remaining"],
        "Litres": [total_produced, total_distributed, remaining_alltime]
    }).set_index("Category")
    st.bar_chart(chart_df)

    # ----------------------------
    # CURRENT MONTH SUMMARY
    # ----------------------------
    now = pd.Timestamp.now()
    current_month_name = now.strftime("%B %Y")
    st.markdown(f"### 📆 Current Month Summary ({current_month_name})")

    def current_month_df(df, date_col="Date"):
        if df is None or df.empty or date_col not in df.columns:
            return pd.DataFrame()
        dts = pd.to_datetime(df[date_col], format="%d-%m-%Y", errors="coerce")
        return df[(dts.dt.month == now.month) & (dts.dt.year == now.year)].copy()

    df_expense_m = current_month_df(df_expense, "Date")
    df_milk_m_m = current_month_df(df_milk_m, "Date")
    df_milk_e_m = current_month_df(df_milk_e, "Date")
    df_cow_log_m = current_month_df(df_cow_log, "Date")

    # current month metrics
    expense_month = df_expense_m["Amount"].sum() if "Amount" in df_expense_m.columns else 0
    dist_m_m = sum_numeric_columns(df_milk_m_m, exclude_cols=["Timestamp", "Date"])
    dist_e_m = sum_numeric_columns(df_milk_e_m, exclude_cols=["Timestamp", "Date"])
    distributed_month = dist_m_m + dist_e_m

    milkcol_m = detect_milk_column(df_cow_log_m)
    milk_produced_month = pd.to_numeric(df_cow_log_m[milkcol_m], errors="coerce").sum() if milkcol_m and milkcol_m in df_cow_log_m.columns else 0
    remaining_month = milk_produced_month - distributed_month

    # bipin fund for current month
    inv_bipin_month = df_invest[df_invest.get("Paid To","").str.contains("Bipin Kumar", case=False, na=False)].copy() if not df_invest.empty and "Paid To" in df_invest.columns else pd.DataFrame()
    pay_bipin_month = df_payment[df_payment.get("Received By","").str.contains("Bipin Kumar", case=False, na=False)].copy() if not df_payment.empty and "Received By" in df_payment.columns else pd.DataFrame()
    exp_bipin_month = df_expense_m[df_expense_m.get("Expense By","").str.contains("Bipin Kumar", case=False, na=False)].copy() if not df_expense_m.empty and "Expense By" in df_expense_m.columns else pd.DataFrame()

    inv_bipin_month_amt = inv_bipin_month.get("Amount", pd.Series(dtype="float")).sum() if not inv_bipin_month.empty else 0
    pay_bipin_month_amt = pay_bipin_month.get("Amount", pd.Series(dtype="float")).sum() if not pay_bipin_month.empty else 0
    exp_bipin_month_amt = exp_bipin_month.get("Amount", pd.Series(dtype="float")).sum() if not exp_bipin_month.empty else 0
    fund_bipin_month = inv_bipin_month_amt + pay_bipin_month_amt - exp_bipin_month_amt

    ccol1, ccol2, ccol3, ccol4 = st.columns(4)
    ccol1.metric("🥛 Produced (This Month)", f"{milk_produced_month:.2f} L")
    ccol2.metric("🚚 Distributed (This Month)", f"{distributed_month:.2f} L")
    ccol3.metric("❗ Remaining / Lost (This Month)", f"{remaining_month:.2f} L")
    ccol4.metric("💰 Expense (This Month)", f"₹{expense_month:,.2f}")

    st.markdown("---")
    st.caption("Recent entries (latest first)")
    r1, r2 = st.columns(2)
    if not df_expense.empty:
        r1.subheader("Expenses")
        r1.dataframe(df_expense.sort_values("Date", ascending=False).head(5), use_container_width=True)
    if not df_payment.empty:
        r2.subheader("Payments")
        r2.dataframe(df_payment.sort_values("Date", ascending=False).head(5), use_container_width=True)

# ----------------------------
# MILKING & FEEDING PAGE
# ----------------------------
elif page == "Milking & Feeding":
    st.title("🐄 Milking & Feeding Log & Analytics")
    st.caption("Per-cow and daily production metrics (from 01-11-2025 onward)")

    df = load_csv(COW_LOG_CSV_URL, drop_cols=["Timestamp"])
    df = filter_from_start_date(df, "Date") if not df.empty else df

    if df.empty:
        st.info("No milking & feeding data available after 01-11-2025.")
    else:
        # detect milk column & normalize numeric
        milk_col = detect_milk_column(df)
        if milk_col:
            df[milk_col] = pd.to_numeric(df[milk_col], errors="coerce")
        # Cow-wise totals
        if "CowID" in df.columns and milk_col:
            cow_wise = df.groupby("CowID")[milk_col].sum().reset_index().rename(columns={milk_col: "Total Milk (L)"}).sort_values("Total Milk (L)", ascending=False)
        else:
            cow_wise = pd.DataFrame()

        # daily totals
        df["Date_dt"] = pd.to_datetime(df["Date"], format="%d-%m-%Y", errors="coerce")
        daily = df.groupby("Date_dt")[milk_col].sum().reset_index().rename(columns={milk_col: "Total Milk (L)"}).sort_values("Date_dt", ascending=False)

        # KPIs
        total_prod = pd.to_numeric(df[milk_col], errors="coerce").sum() if milk_col else 0
        now = pd.Timestamp.now()
        df_this_month = daily[(daily["Date_dt"].dt.month == now.month) & (daily["Date_dt"].dt.year == now.year)]
        produced_this_month = df_this_month["Total Milk (L)"].sum() if not df_this_month.empty else 0

        k1, k2, k3 = st.columns(3)
        k1.metric("🥛 Total Produced (since 01-11-2025)", f"{total_prod:.2f} L")
        k2.metric(f"📅 Produced ({now.strftime('%B %Y')})", f"{produced_this_month:.2f} L")
        k3.metric("📋 Number of Days Recorded", f"{daily['Date_dt'].nunique()}")

        st.markdown("### 🐮 Cow-wise Production")
        if not cow_wise.empty:
            st.dataframe(cow_wise, use_container_width=True)
        else:
            st.info("No CowID column or no cow-wise data available.")

        st.markdown("### 📅 Daily Production Trend")
        if not daily.empty:
            st.line_chart(daily.set_index("Date_dt"))
        else:
            st.info("No daily production data available to plot.")

        st.markdown("### 📋 Raw Milking & Feeding Data")
        st.dataframe(df.sort_values("Date", ascending=False), use_container_width=True)

# ----------------------------
# MILK DISTRIBUTION PAGE
# ----------------------------
elif page == "Milk Distribution":
    st.title("🥛 Milk Distribution")
    st.caption("Totals, daily validation and remaining/loss calculations (from 01-11-2025)")

    df_morning = load_csv(MILK_DIS_M_CSV_URL, drop_cols=["Timestamp"])
    df_evening = load_csv(MILK_DIS_E_CSV_URL, drop_cols=["Timestamp"])
    df_cow_log = load_csv(COW_LOG_CSV_URL, drop_cols=["Timestamp"])

    df_morning = filter_from_start_date(df_morning, "Date") if not df_morning.empty else df_morning
    df_evening = filter_from_start_date(df_evening, "Date") if not df_evening.empty else df_evening
    df_cow_log = filter_from_start_date(df_cow_log, "Date") if not df_cow_log.empty else df_cow_log

    # Totals
    total_morning = sum_numeric_columns(df_morning, exclude_cols=["Timestamp", "Date"])
    total_evening = sum_numeric_columns(df_evening, exclude_cols=["Timestamp", "Date"])
    total_distributed = total_morning + total_evening

    # Monthly distributed
    now = pd.Timestamp.now()
    def monthly_sum(df):
        if df is None or df.empty or "Date" not in df.columns:
            return 0
        dt = pd.to_datetime(df["Date"], format="%d-%m-%Y", errors="coerce")
        dfm = df[(dt.dt.month == now.month) & (dt.dt.year == now.year)]
        return sum_numeric_columns(dfm, exclude_cols=["Timestamp", "Date"])
    distributed_month = monthly_sum(df_morning) + monthly_sum(df_evening)

    # Produced this month (from cow_log)
    milk_col = detect_milk_column(df_cow_log)
    produced_month = 0
    if milk_col and "Date" in df_cow_log.columns:
        df_cow_log["Date_dt"] = pd.to_datetime(df_cow_log["Date"], format="%d-%m-%Y", errors="coerce")
        df_prod_month = df_cow_log[(df_cow_log["Date_dt"].dt.month == now.month) & (df_cow_log["Date_dt"].dt.year == now.year)]
        produced_month = pd.to_numeric(df_prod_month[milk_col], errors="coerce").sum()

    remaining_month = produced_month - distributed_month

    # KPIs
    c1, c2, c3 = st.columns(3)
    c1.metric("🥛 Total Distributed (since 01-11-2025)", f"{total_distributed:.2f} L")
    c2.metric(f"📅 Distributed ({now.strftime('%B %Y')})", f"{distributed_month:.2f} L")
    c3.metric("❗ Remaining (This Month)", f"{remaining_month:.2f} L")

    st.markdown("### 🌅 Morning Distribution (latest first)")
    if not df_morning.empty:
        st.dataframe(df_morning.sort_values("Date", ascending=False), use_container_width=True)
    else:
        st.info("No morning distribution data after 01-11-2025.")

    st.markdown("### 🌇 Evening Distribution (latest first)")
    if not df_evening.empty:
        st.dataframe(df_evening.sort_values("Date", ascending=False), use_container_width=True)
    else:
        st.info("No evening distribution data after 01-11-2025.")

    # Daily comparison table: produced vs distributed vs remaining (for dates present)
    st.markdown("### 📋 Daily Produced vs Distributed")
    if not df_cow_log.empty:
        # build daily produced
        df_cow_log["Date_dt"] = pd.to_datetime(df_cow_log["Date"], format="%d-%m-%Y", errors="coerce")
        if milk_col in df_cow_log.columns:
            daily_produced = df_cow_log.groupby("Date_dt")[milk_col].sum().reset_index().rename(columns={milk_col: "Produced"})
        else:
            daily_produced = pd.DataFrame(columns=["Date_dt", "Produced"])

        # build daily distributed combining morning & evening numeric columns
        def daily_total_from_dist(df_dist):
            if df_dist is None or df_dist.empty:
                return pd.DataFrame(columns=["Date_dt", "Distributed"])
            df_dist["Date_dt"] = pd.to_datetime(df_dist["Date"], format="%d-%m-%Y", errors="coerce")
            # sum all numeric customer columns per row
            numeric_cols = df_dist.select_dtypes(include="number").columns.tolist()
            if not numeric_cols:
                # fallback: try all non-date columns as numeric
                numeric_cols = [c for c in df_dist.columns if c not in ["Date", "Timestamp", "Date_dt"]]
            df_dist["row_total"] = df_dist[numeric_cols].apply(pd.to_numeric, errors="coerce").sum(axis=1)
            return df_dist.groupby("Date_dt")["row_total"].sum().reset_index().rename(columns={"row_total": "Distributed"})

        daily_morn = daily_total_from_dist(df_morning)
        daily_eve = daily_total_from_dist(df_evening)
        daily_dist = pd.merge(daily_morn, daily_eve, on="Date_dt", how="outer").fillna(0)
        if "Distributed_x" in daily_dist.columns and "Distributed_y" in daily_dist.columns:
            # combine if merge created two columns
            daily_dist["Distributed"] = daily_dist.get("Distributed_x", 0) + daily_dist.get("Distributed_y", 0)
            daily_dist = daily_dist[["Date_dt", "Distributed"]]

        # merge produced & distributed
        daily_compare = pd.merge(daily_produced, daily_dist, on="Date_dt", how="outer").fillna(0)
        daily_compare["Remaining"] = daily_compare["Produced"] - daily_compare["Distributed"]
        if not daily_compare.empty:
            daily_compare = daily_compare.sort_values("Date_dt", ascending=False)
            st.dataframe(daily_compare.rename(columns={"Date_dt": "Date"}).assign(Date=lambda d: d["Date"].dt.strftime("%d-%m-%Y")), use_container_width=True)
        else:
            st.info("No daily comparison data available (check columns).")
    else:
        st.info("No production data available to compare with distribution.")

# ----------------------------
# EXPENSE PAGE
# ----------------------------
elif page == "Expense":
    st.title("💸 Expense Tracker")

    df_expense = load_csv(EXPENSE_CSV_URL, drop_cols=["Timestamp"])
    df_expense = filter_from_start_date(df_expense, "Date") if not df_expense.empty else df_expense

    if df_expense.empty:
        st.info("No expense records found (after 01-11-2025).")
    else:
        # ensure Date and Amount
        if "Date" in df_expense.columns:
            df_expense["Date_dt"] = pd.to_datetime(df_expense["Date"], format="%d-%m-%Y", errors="coerce")
            df_expense = df_expense.sort_values("Date_dt", ascending=False)

        total_expense = df_expense["Amount"].sum() if "Amount" in df_expense.columns else 0

        # current month
        now = pd.Timestamp.now()
        df_month = df_expense[df_expense["Date_dt"].dt.month == now.month] if "Date_dt" in df_expense.columns else pd.DataFrame()
        monthly_expense = df_month["Amount"].sum() if not df_month.empty and "Amount" in df_month.columns else 0

        st.metric("💰 Total Expense (since 01-11-2025)", f"₹{total_expense:,.2f}")
        st.metric(f"💳 Expense ({now.strftime('%B %Y')})", f"₹{monthly_expense:,.2f}")

        st.markdown("### 📊 Expense by Type")
        if "Expense Type" in df_expense.columns:
            by_type = df_expense.groupby("Expense Type")["Amount"].sum().sort_values(ascending=False)
            st.bar_chart(by_type)
        else:
            st.info("No 'Expense Type' column to aggregate.")

        st.markdown("### 👤 Expense by Person")
        if "Expense By" in df_expense.columns:
            by_person = df_expense.groupby("Expense By")["Amount"].sum().sort_values(ascending=False)
            st.bar_chart(by_person)
        else:
            st.info("No 'Expense By' column to aggregate.")

        st.markdown("### 📋 Detailed Expense Records")
        st.dataframe(df_expense, use_container_width=True)

# ----------------------------
# PAYMENTS PAGE
# ----------------------------
elif page == "Payments":
    st.title("💰 Payments Record")
    df_payment = load_csv(PAYMENT_CSV_URL, drop_cols=["Timestamp"])
    df_payment = filter_from_start_date(df_payment, "Date") if not df_payment.empty else df_payment
    if df_payment.empty:
        st.info("No payment records found (after 01-11-2025).")
    else:
        if "Date" in df_payment.columns:
            df_payment["Date_dt"] = pd.to_datetime(df_payment["Date"], format="%d-%m-%Y", errors="coerce")
            df_payment = df_payment.sort_values("Date_dt", ascending=False)
        st.dataframe(df_payment, use_container_width=True)

# ----------------------------
# INVESTMENTS PAGE
# ----------------------------
elif page == "Investments":
    st.title("📈 Investment Log")
    df_invest = load_csv(INVESTMENT_CSV_URL, drop_cols=["Timestamp"])
    df_invest = filter_from_start_date(df_invest, "Date") if not df_invest.empty else df_invest
    if df_invest.empty:
        st.info("No investment data found (after 01-11-2025).")
    else:
        if "Date" in df_invest.columns:
            df_invest["Date_dt"] = pd.to_datetime(df_invest["Date"], format="%d-%m-%Y", errors="coerce")
            df_invest = df_invest.sort_values("Date_dt", ascending=False)
        st.dataframe(df_invest, use_container_width=True)

# ----------------------------
# REFRESH BUTTON
# ----------------------------
if st.sidebar.button("🔁 Refresh"):
    st.experimental_rerun()
