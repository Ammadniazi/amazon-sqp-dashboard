import streamlit as st
import pandas as pd
import plotly.express as px

# --- APP CONFIG ---
st.set_page_config(layout="wide", page_title="Amazon SQP Pro")
st.title("📊 Amazon SQP Interactive Dashboard")

# --- DATA LOADING ---
uploaded_file = st.sidebar.file_uploader("Upload your SQP .csv file", type="csv")

if uploaded_file:
    # Based on your input: Row 1 is metadata, Row 2 is headers. 
    # skiprows=1 skips Row 1; header=0 then makes the new first row (Row 2) the header.
    df = pd.read_csv(uploaded_file, skiprows=1, header=0)
    
    # Clean up column names (strip whitespace just in case)
    df.columns = df.columns.str.strip()

    # 1. TIME-SERIES ANALYSIS SECTION
    st.header("📈 Funnel Share Analysis")
    
    col1, col2 = st.columns()
    with col1:
        # Dropdown for Search Query
        all_queries = sorted(df['Search Query'].unique())
        selected_query = st.selectbox("Select Search Query", all_queries)
        
        # Multiselect for Y-axis parameters
        metrics = st.multiselect(
            "Select Data Parameters", 
            ['Impressions: ASIN Share %', 'Clicks: ASIN Share %', 
             'Cart Adds: ASIN Share %', 'Purchases: ASIN Share %'],
            default=['Purchases: ASIN Share %']
        )

    # Filter data for the selected query
    # Note: If your file is a single week, this will show a single point. 
    # If you combine multiple weeks into one file, it will show a trend line.
    query_data = df[df['Search Query'] == selected_query]
    
    fig_line = px.line(query_data, x='Reporting Date', y=metrics, 
                       title=f"Performance for: {selected_query}", markers=True)
    st.plotly_chart(fig_line, use_container_width=True)

    st.divider()

    # 2. PRICE SCANNER SECTION
    st.header("🎯 Price Scanner")
    st.write("Visualizing the Top 50 Search Queries by Volume")
    
    col_s1, col_s2 = st.columns()
    
    with col_s1:
        asin_price = st.number_input("Enter your current ASIN Price ($)", value=25.0)
        tolerance = st.slider("Price Tolerance Toggle (%)", 0, 100, 20)
    
    # Range Calculation
    low_bound = asin_price * (1 - tolerance/100)
    high_bound = asin_price * (1 + tolerance/100)
    
    # Take Top 50 by Volume
    top_50 = df.nlargest(50, 'Search Query Volume').copy()
    
    # Filtering queries where median prices fall within the toggle range
    filtered_queries = top_50[
        (top_50['Purchases: Price (Median)'].between(low_bound, high_bound)) |
        (top_50['Clicks: Price (Median)'].between(low_bound, high_bound)) |
        (top_50['Cart Adds: Price (Median)'].between(low_bound, high_bound))
    ]

    with col_s2:
        fig_scatter = px.scatter(
            filtered_queries, 
            x='Search Query', 
            y=['Clicks: Price (Median)', 'Cart Adds: Price (Median)', 'Purchases: Price (Median)'],
            title=f"Price Distribution (Range: ${low_bound:.2f} - ${high_bound:.2f})",
            labels={"value": "Median Price ($)", "variable": "Metric"}
        )
        # Add a reference line for your ASIN Price
        fig_scatter.add_hline(y=asin_price, line_dash="dot", line_color="red", annotation_text="Your ASIN Price")
        st.plotly_chart(fig_scatter, use_container_width=True)

    # Raw Data View
    with st.expander("View Filtered Data Table"):
        st.dataframe(filtered_queries)

else:
    st.info("Please upload the SQP CSV file to populate the dashboard.")
