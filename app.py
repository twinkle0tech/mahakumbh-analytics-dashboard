
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="Mahakumbh Footfall Dashboard", layout="wide")

@st.cache_data
def load_data(path="Mahakumbh_Footfall_Analytics.csv"):
    df = pd.read_csv(path)
    for col in df.columns:
        if 'date' in col.lower() or 'day' in col.lower() and df[col].dtype == object:
            try:
                df[col] = pd.to_datetime(df[col], errors='coerce')
            except Exception:
                pass
    if 'Date' in df.columns and not np.issubdtype(df['Date'].dtype, np.datetime64):
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    return df

df = load_data()

# Basic defensive checks and auto-detect columns used by dashboard
col1, col2 = st.columns([1, 8])
with col1:
    st.image("logo.png", width=80)  
with col2:
    st.markdown("<h1 style='margin:0;'>MAHAKUMBH MELA 2025 — Footfall Analytics</h1>", unsafe_allow_html=True)


# Sidebar filters
with st.sidebar:
    st.header("Filters")
    # Date range filter if Date column exists
    if 'Date' in df.columns:
        min_date = df['Date'].min()
        max_date = df['Date'].max()
        date_range = st.date_input("Date range", value=(min_date.date() if pd.notna(min_date) else None,
                                                       max_date.date() if pd.notna(max_date) else None))
    else:
        date_range = None

    # Ghat filter
    ghat_col = None
    possible_ghat_cols = [c for c in df.columns if 'ghat' in c.lower() or 'ghat_name' in c.lower()]
    if len(possible_ghat_cols):
        ghat_col = possible_ghat_cols[0]
        ghats = ['All'] + sorted(df[ghat_col].dropna().unique().tolist())
        selected_ghat = st.selectbox("Ghat", ghats, index=0)
    else:
        selected_ghat = 'All'

    # Peak hour filter if exists
    peak_col = [c for c in df.columns if 'peak' in c.lower()]
    peak_col = peak_col[0] if peak_col else None
    if peak_col:
        peak_options = ['All'] + sorted(df[peak_col].dropna().unique().tolist())
        selected_peak = st.selectbox("Peak Hours", peak_options, index=0)
    else:
        selected_peak = 'All'

    # Weather condition filter if exists
    weather_col = [c for c in df.columns if 'weather' in c.lower()]
    weather_col = weather_col[0] if weather_col else None
    if weather_col:
        weather_opts = ['All'] + sorted(df[weather_col].dropna().unique().tolist())
        selected_weather = st.selectbox("Weather condition", weather_opts, index=0)
    else:
        selected_weather = 'All'
    st.markdown("---")
    st.write("Tip: Use filters then scroll main page to view charts.")

# Apply filters
df_viz = df.copy()
if date_range and 'Date' in df_viz.columns and all(date_range):
    start, end = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
    df_viz = df_viz[(df_viz['Date'] >= start) & (df_viz['Date'] <= end)]

if ghat_col and selected_ghat != 'All':
    df_viz = df_viz[df_viz[ghat_col] == selected_ghat]

if peak_col and selected_peak != 'All':
    df_viz = df_viz[df_viz[peak_col] == selected_peak]

if weather_col and selected_weather != 'All':
    df_viz = df_viz[df_viz[weather_col] == selected_weather]


# Detect footfall column BEFORE KPI section
footfall_cols = [c for c in df_viz.columns if 'footfall' in c.lower() or 'total_footfall' in c.lower()]
footfall_col = footfall_cols[0] if footfall_cols else None

# KPI row (safe handling for empty/NaN results)
kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns([1,1,1,1,1])

def safe_int_metric(series, agg="max"):
    if series is None:
        return "—"
    if series.empty:
        return "No data"
    val = series.max() if agg == "max" else series.sum() if agg=="sum" else series.mean()
    if pd.isna(val):
        return "No data"
    try:
        return f"{int(val):,}"
    except Exception:
        # fallback for floats that are not convertible to int
        return f"{val:,.2f}"

def safe_percent(series):
    if series is None or series.empty:
        return "—"
    val = series.mean()
    if pd.isna(val):
        return "No data"
    return f"{val:.2f}%"

with kpi1:
    st.markdown("**Peak hour footfall**")
    if footfall_col is not None:
        st.metric("", safe_int_metric(df_viz[footfall_col], agg="max"))
    else:
        st.metric("", "—")

with kpi2:
    st.markdown("**Total_Footfall**")
    if footfall_col is not None:
        st.metric("", safe_int_metric(df_viz[footfall_col], agg="sum"))
    else:
        st.metric("", "—")

with kpi3:
    st.markdown("**Foreign Visitors %**")
    foreign_col = [c for c in df_viz.columns if 'foreign' in c.lower()]
    if foreign_col:
        st.metric("", safe_percent(df_viz[foreign_col[0]]))
    else:
        st.metric("", "—")

with kpi4:
    st.markdown("**Meal Served Daily (approx)**")
    meal_col = [c for c in df_viz.columns if 'meal' in c.lower() or 'served' in c.lower()]
    if meal_col:
        
        mean_val = df_viz[meal_col[0]].mean()
        st.metric("", "No data" if pd.isna(mean_val) else f"{int(mean_val):,}")
    else:
        st.metric("", "—")

with kpi5:
    st.markdown("**Social Media Mentions (approx)**")
    social_col = [c for c in df_viz.columns if 'social' in c.lower() or 'mentions' in c.lower()]
    if social_col:
        st.metric("", safe_int_metric(df_viz[social_col[0]], agg="sum"))
    else:
        st.metric("", "—")

st.markdown("---")



# Chart 1: Medical Emergencies and Security Incidents by Day (stacked bar)
left_col, mid_col, right_col = st.columns([2,2,1])

with left_col:
    st.subheader("Medical Emergencies and Security Incidents by Day")
    med_col = [c for c in df_viz.columns if 'medical' in c.lower()]
    sec_col = [c for c in df_viz.columns if 'security' in c.lower() or 'incident' in c.lower()]

    
    if 'Day' in df_viz.columns:
        day_col = 'Day'
    elif 'day' in (c.lower() for c in df_viz.columns):
        
        day_col = [c for c in df_viz.columns if c.lower() == 'day'][0]
    elif 'Date' in df_viz.columns and np.issubdtype(df_viz['Date'].dtype, np.datetime64):
        df_viz['DayName'] = df_viz['Date'].dt.day_name()
        day_col = 'DayName'
    else:
        
        df_viz = df_viz.reset_index().rename(columns={'index': 'RowIndex'})
        day_col = 'RowIndex'

    
    cols_for_plot = {}
    if med_col:
        cols_for_plot['Medical Emergencies'] = med_col[0]
    if sec_col:
        cols_for_plot['Security Incidents'] = sec_col[0]

    if not cols_for_plot:
        st.info("No 'medical' or 'security' columns found in the dataset for this chart.")
    else:
       
        agg_df = df_viz.groupby(day_col)[list(cols_for_plot.values())].sum().reset_index()
        plot_df = agg_df.rename(columns={v:k for k,v in cols_for_plot.items()})
        fig = go.Figure()
        if 'Medical Emergencies' in plot_df.columns:
            fig.add_trace(go.Bar(x=plot_df[day_col], y=plot_df['Medical Emergencies'], name='Medical Emergencies'))
        if 'Security Incidents' in plot_df.columns:
            fig.add_trace(go.Bar(x=plot_df[day_col], y=plot_df['Security Incidents'], name='Security Incidents'))
        fig.update_layout(barmode='group', height=350, margin=dict(t=30,b=20,l=0,r=0))
        st.plotly_chart(fig, use_container_width=True)

with mid_col:
    st.subheader("Waste in Tons by Day and Ghat")
    
    waste_cols = [c for c in df_viz.columns if 'waste' in c.lower() or 'trash' in c.lower() or 'tons' in c.lower()]
    if not waste_cols and 'Ghat' in df_viz.columns:
        
        possible = [c for c in df_viz.columns if any(gh.lower() in c.lower() for gh in ['dashashwamedh','ram','har ki','sangam','triveni'])]
        waste_cols = possible[:5]
    if waste_cols:
        
        if ghat_col and 'Date' in df_viz.columns:
            tmp = df_viz.groupby(['Date', ghat_col])[waste_cols[0]].sum().reset_index()
            fig2 = px.bar(tmp, x='Date', y=waste_cols[0], color=ghat_col, height=350)
            fig2.update_layout(margin=dict(t=30,b=20,l=0,r=0))
            st.plotly_chart(fig2, use_container_width=True)
        else:
            agg = df_viz.groupby(day_col)[waste_cols[0]].sum().reset_index()
            fig2 = px.bar(agg, x=day_col, y=waste_cols[0], height=350)
            st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("No waste-related columns detected.")

with right_col:
    st.subheader("Accommodation by Ghat")
    accom_cols = [c for c in df_viz.columns if 'accom' in c.lower() or 'accomm' in c.lower() or 'tent' in c.lower() or 'accommodation' in c.lower()]
    if accom_cols and ghat_col:
        acc = df_viz.groupby(ghat_col)[accom_cols[0]].sum().reset_index()
        fig3 = px.pie(acc, names=ghat_col, values=accom_cols[0], hole=0.45, height=350)
        st.plotly_chart(fig3, use_container_width=True)
    else:
        if ghat_col and footfall_col:
            tmp = df_viz.groupby(ghat_col)[footfall_col].sum().reset_index()
            fig3 = px.pie(tmp, names=ghat_col, values=footfall_col, hole=0.45, height=350)
            st.plotly_chart(fig3, use_container_width=True)
        else:
            st.info("No accommodation or ghat/footfall columns available to build this chart.")

st.markdown("---")
c1, c2 = st.columns([2,2])
with c1:
    st.subheader("Total Footfall by Date")
    if footfall_col and 'Date' in df_viz.columns:
        agg = df_viz.groupby('Date')[footfall_col].sum().reset_index()
        fig = px.line(agg, x='Date', y=footfall_col, height=300)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No Date + Footfall combination found.")

with c2:
    st.subheader("Avg % Footfall over different Ages and Foreign Tourists")
    age_cols = [c for c in df_viz.columns if any(x in c.lower() for x in ['0-18','19-35','36-60','60','age'])]
    foreign_cols = [c for c in df_viz.columns if 'foreign' in c.lower()]
    if age_cols or foreign_cols:
        plotdf = pd.DataFrame()
        xaxis = df_viz['Date'] if 'Date' in df_viz.columns else df_viz.index
        for col in age_cols[:4]:
            try:
                plotdf[col] = df_viz[col]
            except Exception:
                pass
        for col in foreign_cols[:1]:
            plotdf[col] = df_viz[col]
        if not plotdf.empty:
            plotdf['x'] = xaxis
            fig = go.Figure()
            for col in plotdf.columns:
                if col == 'x': continue
                fig.add_trace(go.Scatter(x=plotdf['x'], y=plotdf[col], mode='lines+markers', name=col))
            fig.update_layout(height=300, margin=dict(t=30,b=20,l=0,r=0))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No suitable age/foreign columns detected.")
    else:
        st.info("No age or foreign tourist percentage columns detected.")

st.markdown("---")
b1, b2 = st.columns([2,1])
with b1:
    st.subheader("Total Footfall by Ghat")
    if ghat_col and footfall_col:
        tmp = df_viz.groupby(ghat_col)[footfall_col].sum().reset_index()
        fig = px.treemap(tmp, path=[ghat_col], values=footfall_col, height=400)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No Ghat + Footfall columns to build treemap.")

with b2:
    st.subheader("Quick Data Table (first 10 rows)")
    st.dataframe(df_viz.head(10))

st.markdown("---")
st.caption("This app auto-detects columns by name. If your dataset uses different names, edit the code to match your column names (e.g., 'Total_Footfall', 'Ghat', 'Date', 'Medical_Emergencies').")

@st.cache_data
def convert_df_to_csv(df_in):
    return df_in.to_csv(index=False).encode('utf-8')

csv = convert_df_to_csv(df_viz)
st.download_button("Download filtered dataset (CSV)", data=csv, file_name="filtered_mahakumbh.csv", mime="text/csv")
