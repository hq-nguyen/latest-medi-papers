import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from data_fetcher import get_ai_medicine_news, MEDICAL_AI_TOPICS

# Use Streamlit's built-in caching
@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_data(days=30):
    with st.spinner('Fetching latest AI in Medicine news...'):
        return get_ai_medicine_news(days)

def run_dashboard():
    st.title("AI in Medicine News Dashboard")
    st.subheader("Latest research and news at the intersection of AI and healthcare")
    
    # Settings in sidebar
    st.sidebar.header("Settings")
    days_to_fetch = st.sidebar.slider("Fetch news from past days", 1, 90, 30)
    
    # Add a refresh button
    if st.sidebar.button("Refresh Data"):
        # Clear the cache and get fresh data
        st.cache_data.clear()
        st.rerun()
    
    # Load data with caching
    try:
        df = get_data(days=days_to_fetch)
        
        # Check if df is empty
        if df.empty:
            st.error("No news data available. Please try refreshing later.")
            return
            
        # Get min and max dates
        min_date = df['date'].min()
        max_date = df['date'].max()
        
        # Create filtering options
        st.sidebar.header("Filter Options")
        
        # Date range filter
        selected_dates = st.sidebar.date_input(
            "Date Range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )
        
        # Handle single date selection
        if isinstance(selected_dates, tuple) and len(selected_dates) == 2:
            start_date, end_date = selected_dates
        else:
            start_date = end_date = selected_dates
            
        # Topic filter (using the defined medical AI topics)
        st.sidebar.header("Topics")
        selected_topics = st.sidebar.multiselect(
            "Select topics of interest",
            options=MEDICAL_AI_TOPICS,
            default=[]
        )
        
        # Source filter
        if not df.empty:
            all_sources = sorted(df['Source'].unique().tolist())
            selected_sources = st.sidebar.multiselect(
                "Select sources",
                options=["All"] + all_sources,
                default=["All"]
            )
        
        # Apply filters
        # Convert dates to datetime for filtering
        start_date = pd.to_datetime(start_date)
        end_date = pd.to_datetime(end_date) + timedelta(days=1) - timedelta(seconds=1)  # End of day
        
        # Filter by date range
        df_filtered = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
        
        # Filter by selected sources
        if selected_sources and "All" not in selected_sources:
            df_filtered = df_filtered[df_filtered['Source'].isin(selected_sources)]
        
        # Filter by selected topics
        if selected_topics:
            # Create a boolean mask for articles matching any selected topic
            topic_mask = df_filtered[selected_topics].any(axis=1)
            df_filtered = df_filtered[topic_mask]
        
        # Display results
        if len(df_filtered) > 0:
            st.success(f"Found {len(df_filtered)} articles matching your filters")
            
            # Create tabs for different view options
            tab1, tab2 = st.tabs(["Card View", "Table View"])
            
            with tab1:
                # Show news as cards
                for index, row in df_filtered.iterrows():
                    col1, col2 = st.columns([1, 4])
                    
                    with col1:
                        st.write(f"**{row['date'].strftime('%Y-%m-%d')}**")
                        st.write(f"*{row['Source']}*")
                    
                    with col2:
                        st.markdown(f"### [{row['Title']}]({row['Link']})")
                        st.write(f"{row['Description']}")
                        
                        # Show topics tags for this article
                        article_topics = [topic for topic in MEDICAL_AI_TOPICS if row.get(topic, False)]
                        if article_topics:
                            st.write("**Topics:**", ", ".join(article_topics))
                    
                    st.markdown("---")  # Add separator between cards
            
            with tab2:
                # Create a simplified DataFrame for display
                display_df = df_filtered[['date', 'Title', 'Source', 'Link']].copy()
                display_df['date'] = display_df['date'].dt.strftime('%Y-%m-%d')
                st.dataframe(display_df, column_config={
                    "Link": st.column_config.LinkColumn(),
                }, hide_index=True)
                
        else:
            st.warning("No articles found with the selected filters. Please adjust your filters.")
    
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        st.info("Try refreshing the data using the button in the sidebar.")

if __name__ == '__main__':
    run_dashboard()