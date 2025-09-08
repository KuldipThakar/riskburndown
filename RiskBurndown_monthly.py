import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np


st.set_page_config(page_title="Risk Burndown Chart", layout="wide")
st.title("📉 Risk Burndown Dashboard")

uploaded_file = st.file_uploader("Upload Updated Risk Excel File", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    st.subheader("📄 Data Preview")
    st.dataframe(df)

    try:
        df['Expected End Date (DD-MMM-YY)'] = pd.to_datetime(df['Expected End Date (DD-MMM-YY)'], format="%d-%b-%y", errors='coerce')
        df['Closure Date (DD-MMM-YY)'] = pd.to_datetime(df['Closure Date (DD-MMM-YY)'], format="%d-%b-%y", errors='coerce')
        df['Risk Open Date'] = pd.to_datetime(df['Risk Open Date'], format="%d-%b-%y", errors='coerce')
    except:
        st.error("❌ Date conversion failed. Please make sure all dates are in DD-MMM-YY format.")
        st.stop()

    # Generate timeline for burndown chart
    min_date = df['Risk Open Date'].min()
    max_date = max(df['Expected End Date (DD-MMM-YY)'].max(), df['Closure Date (DD-MMM-YY)'].max())
    timeline = pd.date_range(start=min_date, end=max_date, freq='D')

    expected_counts = []
    actual_counts = []

    for current_date in timeline:
        expected_open = df[
            (df['Risk Open Date'] <= current_date) &
            (df['Expected End Date (DD-MMM-YY)'] > current_date)
        ].shape[0]

        actual_open = df[
            (df['Risk Open Date'] <= current_date) &
            (
                df['Closure Date (DD-MMM-YY)'].isna() |
                (df['Closure Date (DD-MMM-YY)'] > current_date)
            )
        ].shape[0]

        expected_counts.append(expected_open)
        actual_counts.append(actual_open)

    # Plotting burndown chart with bars and lines
    fig, ax = plt.subplots(figsize=(14, 6))
    
    bar_width = 0.45
    timeline_indices = np.arange(len(timeline))
    
    ax.bar(timeline_indices - bar_width/2, expected_counts, width=bar_width, alpha=0.3, color='orange', label="Expected Burndown (Bar)")
    ax.bar(timeline_indices + bar_width/2, actual_counts, width=bar_width, alpha=0.3, color='green', label="Actual Burndown (Bar)")

    ax.plot(timeline_indices, expected_counts, linestyle='--', color='orange', linewidth=2, label="Expected Burndown (Line)")
    ax.plot(timeline_indices, actual_counts, color='green', linewidth=2, label="Actual Burndown (Line)")

    ax.set_title("📉 Risk Burndown Chart with Bars and Lines")
    ax.set_xlabel("Date")
    ax.set_ylabel("Number of Open Risks")
    ax.set_xticks(timeline_indices[::30])
    ax.set_xticklabels(timeline[::30].strftime('%d-%b-%y'), rotation=45)
    ax.legend()
    ax.grid(True)

    st.pyplot(fig)

    # Monthly RPM Calculation and Expected vs Actual Open Risks
    st.subheader("📈 Monthly RPM (Risks Per Month)")
    df['YearMonth'] = df['Risk Open Date'].dt.to_period('M')
    monthly_risks_opened = df.groupby('YearMonth').size()
    avg_rpm = monthly_risks_opened.mean()

    # Generate monthly timeline
    monthly_timeline = pd.period_range(start=min_date.to_period('M'), end=max_date.to_period('M'), freq='M')
    
    monthly_expected_open = []
    monthly_actual_open = []

    for month in monthly_timeline:
        month_start = month.to_timestamp()
        month_end = (month + 1).to_timestamp() - pd.Timedelta(days=1)
        
        expected_open = df[
            (df['Risk Open Date'] <= month_end) &
            (df['Expected End Date (DD-MMM-YY)'] > month_end)
        ].shape[0]
        
        actual_open = df[
            (df['Risk Open Date'] <= month_end) &
            (
                df['Closure Date (DD-MMM-YY)'].isna() |
                (df['Closure Date (DD-MMM-YY)'] > month_end)
            )
        ].shape[0]
        
        monthly_expected_open.append(expected_open)
        monthly_actual_open.append(actual_open)

    # Create DataFrame for monthly metrics
    monthly_rpm_df = pd.DataFrame({
        'YearMonth': [str(m) for m in monthly_timeline],
        'Risks Opened': monthly_risks_opened.reindex(monthly_timeline, fill_value=0).values,
        'Expected Open Risks': monthly_expected_open,
        'Actual Open Risks': monthly_actual_open
    })

    # Plotting monthly RPM chart
    st.subheader("📊 Monthly Risk Metrics Chart")
    fig2, ax2 = plt.subplots(figsize=(14, 6))
    
    bar_width = 0.25  # Narrower bars to fit three metrics
    month_indices = np.arange(len(monthly_timeline))
    
    ax2.bar(month_indices - bar_width, monthly_rpm_df['Risks Opened'], width=bar_width, alpha=0.5, color='blue', label="Risks Opened")
    ax2.bar(month_indices, monthly_rpm_df['Expected Open Risks'], width=bar_width, alpha=0.5, color='orange', label="Expected Open Risks")
    ax2.bar(month_indices + bar_width, monthly_rpm_df['Actual Open Risks'], width=bar_width, alpha=0.5, color='green', label="Actual Open Risks")

    ax2.set_title("📈 Monthly Risks: Opened, Expected Open, and Actual Open")
    ax2.set_xlabel("Year-Month")
    ax2.set_ylabel("Number of Risks")
    ax2.set_xticks(month_indices)
    ax2.set_xticklabels(monthly_rpm_df['YearMonth'], rotation=45)
    ax2.legend()
    ax2.grid(True)

    st.pyplot(fig2)

    st.markdown(f"""
    - 📅 **Average Risks Opened Per Month (RPM)**: {avg_rpm:.2f}
    """)
    
    st.write("Monthly Risk Details (Opened, Expected Open, Actual Open):")
    st.dataframe(monthly_rpm_df.set_index('YearMonth'))

    # Summary stats
    st.subheader("📊 Summary")
    total_risks = df.shape[0]
    closed_risks = df['Closure Date (DD-MMM-YY)'].notna().sum()
    open_risks = total_risks - closed_risks

    st.markdown(f"""
    - 🟢 **Total Risks**: {total_risks}  
    - 🔴 **Currently Open Risks**: {open_risks}  
    - ✅ **Closed Risks**: {closed_risks}
    """)

else:
    st.info("📤 Please upload the cleaned Excel file to generate the chart.")