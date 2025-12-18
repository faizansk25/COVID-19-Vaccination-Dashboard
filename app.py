# app.py

import streamlit as st
import pandas as pd
import plotly.express as px

# ----------------- PAGE CONFIG -----------------
st.set_page_config(
    page_title="COVID-19 Vaccination Dashboard",
    page_icon="💉",
    layout="wide"
)

# ----------------- DATA LOADING & CLEANING -----------------
@st.cache_data
def load_data():
    # Load the optimized parquet file
    # Ensure you have run the notebook or optimization script to generate this file
    try:
        df = pd.read_parquet('cleaned_vaccinations.parquet')
    except FileNotFoundError:
        st.error("Data file not found. Please run the data preparation notebook first.")
        st.stop()
    return df

df = load_data()

# ----------------- SIDEBAR -----------------
st.sidebar.header("Filter Options")

# Location Selection
non_country_aggregates = ['World', 'Europe', 'Asia', 'Africa', 'North America', 
                          'South America', 'European Union', 'High income', 
                          'Low income', 'Lower middle income', 'Upper middle income']
                          
country_list = sorted([loc for loc in df['location'].unique() if loc not in non_country_aggregates])
location_options = ["Worldwide"] + country_list

selected_option = st.sidebar.selectbox(
    "Select a Location",
    location_options
)

# Date Range Filter
min_date = df['date'].min().date()
max_date = df['date'].max().date()

start_date, end_date = st.sidebar.date_input(
    "Select Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

# Filter Data
if selected_option == "Worldwide":
    location_to_filter = "World"
else:
    location_to_filter = selected_option

# Filter by location
filtered_df = df[df['location'] == location_to_filter].copy()

# Filter by date
filtered_df = filtered_df[
    (filtered_df['date'].dt.date >= start_date) & 
    (filtered_df['date'].dt.date <= end_date)
]

# ----------------- MAIN PAGE -----------------
st.title("💉 COVID-19 Vaccination Dashboard")
st.markdown(f"**Location:** {selected_option} | **Date Range:** {start_date} to {end_date}")

if filtered_df.empty:
    st.warning("No data available for the selected filters.")
    st.stop()

# ----------------- KEY METRICS -----------------
latest_data = filtered_df.iloc[-1]

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Vaccinations", f"{int(latest_data['total_vaccinations']):,}")

with col2:
    st.metric("People Fully Vaccinated", f"{int(latest_data['people_fully_vaccinated']):,}")

with col3:
    st.metric("Total Boosters", f"{int(latest_data['total_boosters']):,}")

with col4:
    coverage = latest_data['people_fully_vaccinated_per_hundred']
    st.metric("Fully Vaccinated %", f"{coverage:.2f}%")

st.progress(min(coverage / 100, 1.0))

st.markdown("---")

# ----------------- VISUALIZATIONS -----------------
tab1, tab2, tab3 = st.tabs(["Trends", "Comparisons", "Global View"])

with tab1:
    st.subheader("Vaccination Trends Over Time")
    
    # Total Vaccinations Area Chart
    fig_total = px.area(
        filtered_df, 
        x='date', 
        y='total_vaccinations', 
        title='Cumulative Total Vaccinations'
    )
    st.plotly_chart(fig_total, use_container_width=True)
    
    # Daily Vaccinations Line Chart
    fig_daily = px.line(
        filtered_df,
        x='date',
        y='daily_vaccinations',
        title='Daily Vaccinations Trend'
    )
    st.plotly_chart(fig_daily, use_container_width=True)

with tab2:
    st.subheader("Vaccination Breakdown")
    
    # Comparison of Vaccinated vs Fully Vaccinated
    # We create a melted dataframe for the group bar chart
    comparison_cols = ['people_vaccinated', 'people_fully_vaccinated']
    
    # Clean data for plotting (ensure latest metrics are consistent)
    # We take the latest row for the bar chart comparison
    latest_comparison = filtered_df.iloc[[-1]][['location'] + comparison_cols].melt(id_vars='location', var_name='Metric', value_name='Count')
    
    fig_compare = px.bar(
        latest_comparison,
        x='Metric',
        y='Count',
        color='Metric',
        title=f"Initial vs Full Vaccination in {selected_option}",
        text_auto='.2s'
    )
    st.plotly_chart(fig_compare, use_container_width=True)

with tab3:
    if selected_option == "Worldwide":
        st.subheader("Global Comparisons")
        
        # Get latest data for all countries
        # Filter for the selected date range's end date to be fair, or just strict latest available
        # Here we take the max date available in the entire dataset for each country to show "current status"
        # However, to respect the date filter, we might want to take the max date within the range.
        
        subset_df = df[
            (df['date'].dt.date <= end_date) & 
            (~df['location'].isin(non_country_aggregates))
        ]
        # Get latest entry per country within the filtered date
        latest_country_data = subset_df.sort_values('date').groupby('location').tail(1)
        
        # Top 10 Countries by Total Vaccinations
        top_10 = latest_country_data.nlargest(10, 'total_vaccinations')
        
        fig_top10 = px.bar(
            top_10,
            x='total_vaccinations',
            y='location',
            orientation='h',
            title=f"Top 10 Most Vaccinated Countries (by Total Doses) as of {end_date}",
            color='total_vaccinations',
            color_continuous_scale='Viridis'
        )
        # Invert y axis to show highest on top
        fig_top10.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_top10, use_container_width=True)
        
        # Map
        st.subheader("Global Vaccination Coverage Map")
        fig_map = px.choropleth(
            latest_country_data,
            locations="iso_code",
            color="people_fully_vaccinated_per_hundred",
            hover_name="location",
            color_continuous_scale=px.colors.sequential.Plasma,
            title="Percentage of Population Fully Vaccinated"
        )
        st.plotly_chart(fig_map, use_container_width=True)
        
    else:
        st.info("Select 'Worldwide' in the sidebar to view global comparisons and rankings.")