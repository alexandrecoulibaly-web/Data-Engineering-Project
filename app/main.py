import streamlit as st
from pymongo import MongoClient
import pandas as pd
import plotly.express as px
import os

# Configuration
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DATABASE_NAME = "ubisoft_db"
COLLECTION_NAME = "games"

# Page Config
st.set_page_config(
    page_title="Ubisoft Games Explorer",
    layout="wide"
)

# Database Connection
@st.cache_resource
def init_connection():
    return MongoClient(MONGO_URI)

client = init_connection()
db = client[DATABASE_NAME]
collection = db[COLLECTION_NAME]

# Data Fetching
def get_data():
    items = list(collection.find())
    return items

data = get_data()

# Title and Description
st.title("Ubisoft Games Explorer")
st.markdown("Explore the latest games scraped from the [Ubisoft Store](https://store.ubisoft.com/fr/games).")

if not data:
    st.warning("No data found in the database. Please make sure the scraper has run.")
else:
    # Convert to DataFrame for easier manipulation
    df = pd.DataFrame(data)

    # Sidebar Filters
    st.sidebar.header("Filters")
    
    # Search
    search_query = st.sidebar.text_input("Search Games", "").lower()
    
    # On Sale Filter
    show_only_sales = st.sidebar.checkbox("Show Only Games on Sale", value=False)
    
    # Genre Filter
    if 'genres' in df.columns:
        # Flatten all genres from all games into a unique list
        all_genres = []
        for genres_list in df['genres'].dropna():
            if isinstance(genres_list, list):
                all_genres.extend(genres_list)
        all_genres = sorted(list(set(all_genres)))
        selected_genres = st.sidebar.multiselect("Genre", all_genres, default=all_genres)
    else:
        selected_genres = []
        
    # Price Filter
    if 'unit_price' in df.columns:
        min_price = float(df['unit_price'].min())
        max_price = float(df['unit_price'].max())
        price_range = st.sidebar.slider("Price Range (€)", min_price, max_price, (min_price, max_price))
    else:
        price_range = (0, 0)

    # Apply Filters
    filtered_df = df.copy()
    
    # On Sale Filter
    if show_only_sales:
        if 'is_on_sale' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['is_on_sale'] == True]
    
    # Search Filter
    if search_query:
        filtered_df = filtered_df[filtered_df['name'].str.lower().str.contains(search_query)]
        
    # Genre Filter
    if 'genres' in df.columns and selected_genres and len(selected_genres) < len(all_genres):
        # Only filter if user has deselected some genres
        # Filter rows where at least one of the selected genres is in the game's genres list
        def has_selected_genre(genres_list):
            if isinstance(genres_list, list) and genres_list:
                return any(genre in selected_genres for genre in genres_list)
            # If genres is missing/empty, don't filter it out (show as uncategorized)
            return False
        filtered_df = filtered_df[filtered_df['genres'].apply(has_selected_genre)]

    # Price Filter
    if 'unit_price' in df.columns:
        filtered_df = filtered_df[
            (filtered_df['unit_price'] >= price_range[0]) & 
            (filtered_df['unit_price'] <= price_range[1])
        ]

    # KPIs
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Games", len(filtered_df))
    
    # Count games on sale
    if 'is_on_sale' in filtered_df.columns:
        on_sale_count = filtered_df['is_on_sale'].sum()
        col2.metric("Games on Sale", int(on_sale_count))
    
    if 'unit_price' in df.columns:
        avg_price = filtered_df['unit_price'].mean()
        col3.metric("Average Price", f"{avg_price:.2f} €")
    col4.metric("Genres Available", len(all_genres) if 'genres' in df.columns and selected_genres else 0)

    # Visualizations
    st.markdown("### Analytics")
    c1, c2 = st.columns(2)
    
    with c1:
        if 'genres' in df.columns:
            genre_list = []
            for genres in filtered_df['genres'].dropna():
                if isinstance(genres, list):
                    genre_list.extend(genres)
            # Count occurrences
            from collections import Counter
            genre_counts = Counter(genre_list)
            genre_df = pd.DataFrame(genre_counts.items(), columns=['Genre', 'Count'])
            genre_df = genre_df.sort_values('Count', ascending=False)
            fig_genre = px.bar(genre_df, x='Genre', y='Count', title="Games by Genre", color='Genre')
            st.plotly_chart(fig_genre, use_container_width=True)
            
    with c2:
        if 'unit_price' in df.columns:
            fig_price = px.histogram(filtered_df, x='unit_price', title="Price Distribution", nbins=20)
            st.plotly_chart(fig_price, use_container_width=True)

    # Games Grid
    st.markdown("### Games Library")
    
    # Display in a grid
    cols = st.columns(4)
    for i, row in filtered_df.reset_index(drop=True).iterrows():
        with cols[i % 4]:
             with st.container(border=True):
                if 'image_url' in row and row['image_url']:
                    try:
                        st.image(row['image_url'], use_container_width=True)
                    except Exception as e:
                        st.error(f"Could not load image")
                        st.caption(f"URL: {row['image_url'][:50]}...")
                st.subheader(row['name'])
                if 'genres' in row and row['genres']:
                    if isinstance(row['genres'], list):
                        genres_str = ", ".join(row['genres'])
                        st.caption(f"**Genre:** {genres_str}")
                    else:
                        st.caption(f"**Genre:** {row['genres']}")
                if 'unit_price' in row:
                    price = row['unit_price']
                    original_price = row.get('original_price', price)
                    
                    if price == 0:
                        st.markdown("**Free**")
                    else:
                        # Check if on sale
                        if 'is_on_sale' in row and row['is_on_sale']:
                            discount = row.get('discount_percentage', 0)
                            st.markdown(f"**SALE: -{discount}%**")
                            st.markdown(f"<span style='color: gray; text-decoration: line-through;'>€{original_price:.2f}</span> <span style='color: red; font-weight: bold; font-size: 1.2em;'>€{price:.2f}</span>", unsafe_allow_html=True)
                        else:
                            # Show both prices even if not on sale
                            if original_price and original_price != price:
                                st.markdown(f"~~€{original_price:.2f}~~ **€{price:.2f}**")
                            else:
                                st.markdown(f"**€{price:.2f}**")
                
                if 'url' in row:
                    st.link_button("View on Store", row['url'])

