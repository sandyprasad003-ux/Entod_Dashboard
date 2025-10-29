import streamlit as st
import pandas as pd
import plotly.express as px
import base64
import os
from datetime import datetime

# -------------------------------
# Helper Functions
# -------------------------------
@st.cache_data
def load_data(file_path):
    if file_path.endswith(("xlsx", "xls")):
        return pd.read_excel(file_path, engine="openpyxl")
    else:
        return pd.read_csv(file_path)

def create_sidebar_filters(df, exclude_cols=None):
    exclude_cols = exclude_cols or []
    filters = {}
    for col in df.columns:
        if col not in exclude_cols and col not in ["Sales Qty", "Sales Amt", "Month"]:
            options = sorted(df[col].dropna().unique())
            options = ["ALL"] + options
            selected = st.sidebar.multiselect(col, options, default=["ALL"], key=f"filter_{col}")
            if "ALL" not in selected:
                filters[col] = selected
    return filters

def apply_filters(df, filters):
    filtered = df.copy()
    for col, sel in filters.items():
        filtered = filtered[filtered[col].isin(sel)]
    return filtered

def format_diff_arrow(value):
    if value > 0:
        return f'<span style="color:green; font-weight:bold;">▲ {value:,.0f}</span>'
    elif value < 0:
        return f'<span style="color:red; font-weight:bold;">▼ {abs(value):,.0f}</span>'
    else:
        return f'<span style="color:gray; font-weight:bold;">0</span>'

# -------------------------------
# Page config
# -------------------------------
st.set_page_config(page_title="Entod Pharma Dashboard", layout="wide")

# -------------------------------
# Top Navigation Buttons
# -------------------------------
if "page" not in st.session_state:
    st.session_state.page = "Current Month Dashboard"

col1, col2 = st.columns(2)
with col1:
    if st.button("📊 Current Month Dashboard"):
        st.session_state.page = "Current Month Dashboard"
with col2:
    if st.button("📈 YoY Sales Comparison"):
        st.session_state.page = "YoY Sales Comparison"

page = st.session_state.page

# -------------------------------
# Load Data
# -------------------------------
current_file = "ALL_DIVISION_DATA_1ST_SEP_24TH_SEP_25_CBO.xlsx"
last_file = "LY_FY24_25_CBO_DATA.xlsx"

if not os.path.exists(current_file) or not os.path.exists(last_file):
    st.error("❌ Required Excel files not found in the app directory.")
    st.write("Please place these files in the app folder:")
    st.code(current_file)
    st.code(last_file)
    st.stop()

df_current = load_data(current_file)
df_last = load_data(last_file)

# Clean string columns
for df_ in [df_current, df_last]:
    for col in df_.select_dtypes(include=["object"]):
        df_[col] = df_[col].astype(str).str.strip()

# Ensure Month exists in last FY and convert to datetime
if "Month" not in df_last.columns:
    st.error("❌ 'Month' column not found in Last FY file.")
    st.stop()
df_last["Month"] = pd.to_datetime(df_last["Month"], errors="coerce")

# -------------------------------
# Header & Logo
# -------------------------------
def show_header():
    try:
        with open("logo.png", "rb") as f:
            logo_bytes = f.read()
        logo_base64 = base64.b64encode(logo_bytes).decode()
        st.markdown(
            f"""
            <div style="background-color:#FF0D0D; padding:15px; border-radius:10px; display:flex; align-items:center; justify-content:center;">
                <img src="data:image/png;base64,{logo_base64}" alt="Company Logo" style="height:50px; margin-right:15px;">
                <h2 style="color:white; margin:0;">Entod Pharma Dashboard</h2>
            </div>
            """,
            unsafe_allow_html=True,
        )
    except FileNotFoundError:
        st.markdown(
            """
            <div style="background-color:#FF0D0D; padding:15px; border-radius:10px; text-align:center;">
                <h2 style="color:white; margin:0;">Entod Pharma Dashboard</h2>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown("<br>", unsafe_allow_html=True)

show_header()

# -------------------------------
# Info marquee / notice
# -------------------------------
st.markdown(
    """
    <marquee behavior="scroll" direction="left" scrollamount="6"
             style="background-color:#FFCCCB; color:black; padding:10px; border-radius:8px; font-size:16px;">
        ⚠️ This Dashboard Is Daily Refreshed at 10 AM and 5 PM.
        You will be able to extract new updated data only after these times.
    </marquee>
    """,
    unsafe_allow_html=True,
)
st.markdown("<br>", unsafe_allow_html=True)

# -------------------------------
# Page: Current Month Dashboard
# -------------------------------
if page == "Current Month Dashboard":
    st.header("Current Month to Till Date Dashboard")

    filters = create_sidebar_filters(df_current)
    metric_options = [col for col in ["Sales Qty", "Sales Amt"] if col in df_current.columns]
    selected_metric = st.sidebar.selectbox("Select Metric", metric_options)
    filtered_df = apply_filters(df_current, filters)

    if selected_metric in filtered_df.columns:
        total_value = filtered_df[selected_metric].sum()
        st.markdown(
            f"""
            <div style="background-color:#FF0D0D; padding:15px; border-radius:10px; text-align:center;">
                <h3 style="color:white; margin:0;">Total {selected_metric}</h3>
                <h2 style="color:white; margin:0;">{total_value:,.2f}</h2>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.error(f"⚠️ '{selected_metric}' column not found in dataset.")

    if "State Name" in filtered_df.columns and selected_metric in filtered_df.columns:
        st.markdown("<br>")
        state_agg = (
            filtered_df.groupby("State Name")[selected_metric]
            .sum()
            .reset_index()
            .sort_values(selected_metric, ascending=False)
            .head(10)
        )
        st.markdown(
            f"""
            <div style="background-color:#FF0D0D; padding:10px; border-radius:10px; text-align:center;">
                <h3 style="color:white; margin:0;">Top 10 States by {selected_metric}</h3>
            </div>
            """,
            unsafe_allow_html=True,
        )
        fig = px.bar(state_agg, x="State Name", y=selected_metric, color_discrete_sequence=["#FF0D0D"])
        st.plotly_chart(fig, use_container_width=True)

    if "Division Name" in filtered_df.columns and selected_metric in filtered_df.columns:
        st.markdown("<br>")
        div_agg = (
            filtered_df.groupby("Division Name")[selected_metric]
            .sum()
            .reset_index()
            .sort_values(selected_metric, ascending=False)
            .head(10)
        )
        st.markdown(
            f"""
            <div style="background-color:#FF0D0D; padding:10px; border-radius:10px; text-align:center;">
                <h3 style="color:white; margin:0;">Top 10 Divisions by {selected_metric}</h3>
            </div>
            """,
            unsafe_allow_html=True,
        )
        fig2 = px.pie(div_agg, values=selected_metric, names="Division Name", hole=0.3)
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("<br>")
    st.markdown(
        """
        <div style="background-color:#FF0D0D; padding:10px; border-radius:10px; text-align:center;">
            <h3 style="color:white; margin:0;">Filtered Data - All Rows</h3>
        </div>
        """,
        unsafe_allow_html=True,
    )

    display_df = filtered_df.copy()
    for c in display_df.select_dtypes(include=["number"]).columns:
        display_df[c] = display_df[c].round(2)

    st.dataframe(display_df, use_container_width=True)

    csv = display_df.to_csv(index=False).encode("utf-8")
    st.download_button("Download filtered data", csv, "filtered.csv", "text/csv")

# -------------------------------
# Page: YoY Sales Comparison
# -------------------------------
elif page == "YoY Sales Comparison":
    st.header("YoY Sales Comparison Dashboard")

    month_opts = sorted(df_last["Month"].dt.strftime("%B-%Y").dropna().unique())
    selected_month = st.sidebar.selectbox("Select Month for YoY Comparison", month_opts)

    filters = create_sidebar_filters(df_current, exclude_cols=["Month", "Sales Qty", "Sales Amt"])
    filtered_current = apply_filters(df_current, filters)
    filtered_last = apply_filters(df_last, filters)
    filtered_last = filtered_last[filtered_last["Month"].dt.strftime("%B-%Y") == selected_month]

    curr_qty = filtered_current["Sales Qty"].sum()
    last_qty = filtered_last["Sales Qty"].sum()
    diff_qty = curr_qty - last_qty

    curr_amt = filtered_current["Sales Amt"].sum()
    last_amt = filtered_last["Sales Amt"].sum()
    diff_amt = curr_amt - last_amt

    st.markdown(
        """
        <style>
        .kpi-card {
            background-color: #FF0D0D;
            color: white;
            border-radius: 12px;
            padding: 20px;
            margin: 10px;
            text-align: center;
            font-family: Arial, sans-serif;
        }
        .kpi-title { font-size: 18px; font-weight: 600; margin-bottom: 8px; }
        .kpi-value { font-size: 28px; font-weight: 700; }
        .kpi-diff { font-size: 20px; margin-top: 10px; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    cols = st.columns(3)
    with cols[0]:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-title">Sales Quantity (Current)</div>
                <div class="kpi-value">{curr_qty:,.0f}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with cols[1]:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-title">Sales Quantity (Last FY)</div>
                <div class="kpi-value">{last_qty:,.0f}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with cols[2]:
        st.markdown(
            f"""
            <div class="kpi-title" style="color:white; font-weight:600; font-size:18px; margin-bottom:8px;">Qty Difference</div>
            <div class="kpi-diff" style="color:white; font-size:20px; margin-top:10px;">{format_diff_arrow(diff_qty)}</div>
            """,
            unsafe_allow_html=True,
        )

    cols2 = st.columns(3)
    with cols2[0]:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-title">Sales Amount (Current)</div>
                <div class="kpi-value">{curr_amt:,.0f}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with cols2[1]:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-title">Sales Amount (Last FY)</div>
                <div class="kpi-value">{last_amt:,.0f}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with cols2[2]:
        st.markdown(
            f"""
            <div class="kpi-title" style="color:white; font-weight:600; font-size:18px; margin-bottom:8px;">Amt Difference</div>
            <div class="kpi-diff" style="color:white; font-size:20px; margin-top:10px;">{format_diff_arrow(diff_amt)}</div>
            """,
            unsafe_allow_html=True,
        )

    with st.expander("Show Filtered Current Month Data"):
        st.dataframe(filtered_current, use_container_width=True)

    with st.expander(f"Show Filtered Last FY Data for {selected_month}"):
        st.dataframe(filtered_last, use_container_width=True)
