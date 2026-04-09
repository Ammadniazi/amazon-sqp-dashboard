import streamlit as st
import pandas as pd
import plotly.express as px

# --- App Layout ---
st.set_page_config(layout="wide", page_title="Amazon SQP Dashboard")
st.title("🛡️ Amazon SQP Performance & Price Scanner")

# --- Step 1: Load Data ---
uploaded_file = st.sidebar.file_uploader("Upload SQP Report (CSV)", type="csv")

if uploaded_file:
    # Load and cache data for performance
    df = pd.read_csv(uploaded_file)
    
    # Clean data: Ensure columns are numeric
    cols_to_fix = [col for col in df.columns if 'Price' in col or 'Share' in col or 'Count' in col]
    for col in cols_to_fix:
        df[col] = pd.to_numeric(df[col].astype(str).str.replace('%', '').str.replace('$', ''), errors='coerce')

    # --- Step 2: Interactive Line Chart ---
    st.header("📈 Funnel Share Analysis")
    
    queries = df['Search Query'].unique()
    selected_query = st.selectbox("Search Query Selection", queries)
    
    # Filter data for specific query
    query_df = df[df['Search Query'] == selected_query].sort_values('Reporting Week')
    
    # Let user pick metrics for Y-axis
    available_metrics = [
        'Impressions: ASIN Share %', 'Clicks: ASIN Share %', 
        'Cart Adds: ASIN Share %', 'Purchases: ASIN Share %'
    ]
    selected_metrics = st.multiselect("Select Funnel Metrics", available_metrics, default=available_metrics)
    
    fig_line = px.line(query_df, x='Reporting Week', y=selected_metrics, 
                       title=f"Performance Trend for '{selected_query}'", markers=True)
    st.plotly_chart(fig_line, use_container_width=True)

    st.divider()

    # --- Step 3: Price Scanner ---
    st.header("🎯 Price Scanner")
    st.write("Compare your ASIN price against the market median across top 50 queries.")

    col_p1, col_p2 = st.columns()
    with col_p1:
        asin_price = st.number_input("Your ASIN Current Price ($)", value=25.00)
        tolerance = st.slider("Price Tolerance Toggle (%)", 0, 100, 20)
    
    # Filtering Logic
    low_range = asin_price * (1 - tolerance/100)
    high_range = asin_price * (1 + tolerance/100)
    
    # Top 50 queries by volume
    top_50_df = df.nlargest(50, 'Search Query Volume').copy()
    
    # Apply filter based on toggle
    mask = (top_50_df['Purchases: Price (Median)'].between(low_range, high_range))
    filtered_df = top_50_df[mask]

    with col_p2:
        fig_scatter = px.scatter(
            filtered_df, 
            x='Search Query', 
            y='Purchases: Price (Median)',
            size='Search Query Volume',
            color='Purchases: ASIN Share %',
            hover_data=['Clicks: Price (Median)', 'Cart Adds: Price (Median)'],
            title=f"Queries with Median Price between ${low_range:.2f} - ${high_range:.2f}"
        )
        # Add a baseline for your price
        fig_scatter.add_hline(y=asin_price, line_dash="dot", line_color="red", annotation_text="Your ASIN Price")
        st.plotly_chart(fig_scatter, use_container_width=True)

    # Show data table for the filtered queries
    st.subheader("Query Deep-Dive Table")
    st.dataframe(filtered_df)

else:
    st.info("👋 Welcome! Please upload your Amazon SQP report in the sidebar to visualize your data.")
