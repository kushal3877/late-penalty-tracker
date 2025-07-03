
import streamlit as st
import pandas as pd
from datetime import datetime, time

st.title("💵  Penalty Tracker 💵")

uploaded_file = st.file_uploader("Upload Attendance CSV", type="csv")
if uploaded_file:
    df = pd.read_csv(uploaded_file)

    df = df.rename(columns=lambda x: x.strip())
    df['EmpName'] = df['EmpName'].str.strip()
    df['Date'] = df['Date'].str.strip()
    df['1 Punch'] = df['1 Punch'].str.strip()

    df['Date'] = pd.to_datetime(df['Date'], format="%d-%b-%Y", errors='coerce')
    df['1 Punch Time'] = pd.to_datetime(df['1 Punch'], format="%H:%M:%S", errors='coerce').dt.time

    df = df[df['Date'].dt.dayofweek != 5]  # Exclude Saturdays

    late_start = time(9, 31)
    late_end = time(9, 59)
    df_late = df[df['1 Punch Time'].between(late_start, late_end)]

    penalty_records = []
    for emp, group in df_late.groupby('EmpName'):
        group = group.sort_values('Date').reset_index(drop=True)
        total_days = len(group)
        penalty = 0
        daily_penalties = []
        for i in range(total_days):
            if i < 3:
                p = 0
            else:
                block = (i - 3) // 3
                p = 50 * (block + 1)
            penalty += p
            daily_penalties.append(p)

        group['Penalty'] = daily_penalties
        group['Total Late Days'] = total_days
        group['Total Penalty'] = penalty
        group['DateTime'] = group['Date'].dt.strftime('%d-%b-%Y') + ' ' + group['1 Punch Time'].astype(str)
        penalty_records.append(group[['EmpName', 'DateTime', 'Total Late Days', 'Total Penalty']])

    if penalty_records:
        df_summary = pd.concat(penalty_records, ignore_index=True)
        final_df = (
            df_summary.groupby('EmpName')
            .agg({
                'DateTime': lambda x: ', '.join(x),
                'Total Late Days': 'max',
                'Total Penalty': 'max'
            })
            .reset_index()
            .rename(columns={
                'EmpName': 'Employee Name',
                'DateTime': 'Late Dates with Time',
                'Total Late Days': 'Late Days Count',
                'Total Penalty': 'Total Penalty (Rs)'
            })
        )

        st.success("Penalty Summary Generated")
        st.dataframe(final_df)

        csv = final_df.to_csv(index=False).encode('utf-8')
        st.download_button("Download Summary CSV", csv, "late_penalty_summary.csv", "text/csv")
    else:
        st.info("No late entries found between 9:31–9:59 AM.")
