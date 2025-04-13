import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# Ensure Streamlit page configuration is set first
st.set_page_config(page_title="Sales & Stock Dashboard", layout="wide")

# Load CSV files
@st.cache_data
def load_data():
    sales_df = pd.read_csv("Chatbot Pilot - Extract 1.csv", encoding="utf-8")
    stock_g2g_df = pd.read_csv("[SKT & G2G] - Master Stock MTD - [G2G] - Stock.csv", encoding="utf-8")
    stock_skintific_df = pd.read_csv("[SKT & G2G] - Master Stock MTD - [SKT] - Stock.csv", encoding="utf-8")
    
    # Standardize column names (case-insensitive)
    for df in [sales_df, stock_g2g_df, stock_skintific_df]:
        df.columns = df.columns.str.strip().str.lower()

    return sales_df, stock_g2g_df, stock_skintific_df

# Load Data
sales_df, stock_g2g_df, stock_skintific_df = load_data()

# Function to clean and normalize region names
def clean_region(series):
    return series.str.strip().str.replace(r'\s+', ' ', regex=True).str.title()

# Extract unique regions safely and normalize
def get_unique_regions(df, column):
    if column in df.columns:
        return set(clean_region(df[column].dropna().astype(str)))
    return set()

sales_regions = get_unique_regions(sales_df, "region")
stock_g2g_regions = get_unique_regions(stock_g2g_df, "region")
stock_skintific_regions = get_unique_regions(stock_skintific_df, "region")

# Combine all unique regions
all_regions = sorted(sales_regions | stock_g2g_regions | stock_skintific_regions)

# Extract brand/category options
sales_brands = set(sales_df["brand"].dropna().unique()) if "brand" in sales_df.columns else set()
stock_brands = {"SKINTIFIC", "G2G"}  # Define brands explicitly for stock

# Streamlit UI
st.title("📊 Sales & Stock Dashboard")

# Sidebar for selection
st.sidebar.header("Filter Options")
data_type = st.sidebar.selectbox("Select Data Type", ["Sales", "Stock"])
brand = st.sidebar.selectbox("Select Brand", sorted(sales_brands | stock_brands))  # Merge sales & stock brands
region = st.sidebar.selectbox("Select Region", all_regions)

# Filter data based on selection
if data_type == "Sales":
    if "region" in sales_df.columns and "nettamountinctax" in sales_df.columns and "orderdate" in sales_df.columns and "brand" in sales_df.columns:
        sales_df["region"] = clean_region(sales_df["region"])
        sales_df["brand"] = sales_df["brand"].str.strip().str.upper()  # Standardize brand names
        sales_df["nettamountinctax"] = pd.to_numeric(sales_df["nettamountinctax"], errors="coerce")  # Convert to numeric
        sales_df["orderdate"] = pd.to_datetime(sales_df["orderdate"], errors="coerce")  # Convert OrderDate to datetime

        # Filter for the selected region & brand
        filtered_df = sales_df[(sales_df["region"] == region) & (sales_df["brand"] == brand)]

        # Sum total sales for the region & brand
        total_sales = filtered_df["nettamountinctax"].sum()

        # Display the total sales in Streamlit
        st.metric(label=f"Total Sales in {region} ({brand})", value=f"Rp {total_sales:,.0f}")

        # Show summary statistics
        st.subheader(f"Sales Summary for {region} ({brand})")
        if not filtered_df.empty:
            st.write(filtered_df["nettamountinctax"].describe())
        else:
            st.warning(f"No data available for {region} ({brand})")

        # Sales trend over time (by day)
        st.subheader(f"Sales Trend for {region} ({brand}) Over Time")

        # Group by order date and sum the sales by day
        sales_trend = filtered_df.groupby(filtered_df["orderdate"].dt.date)["nettamountinctax"].sum().reset_index()

        # Plot the sales trend by day
        plt.figure(figsize=(12, 6))
        plt.bar(sales_trend["orderdate"].astype(str), sales_trend["nettamountinctax"], color='skyblue')
        plt.xlabel("Date", fontsize=12)
        plt.ylabel("Total Sales (Rp)", fontsize=12)
        plt.title(f"Sales Trend for {region} ({brand})", fontsize=16)
        plt.xticks(rotation=45)
        st.pyplot(plt)

    else:
        st.error("Sales dataset is missing required columns.")

else:
    # Select the appropriate stock dataset based on brand
    if brand == "SKINTIFIC":
        stock_df = stock_skintific_df.copy()
    else:  # brand == "G2G"
        stock_df = stock_g2g_df.copy()

    if "region" in stock_df.columns and "stock" in stock_df.columns and "stock date" in stock_df.columns:
        stock_df["region"] = clean_region(stock_df["region"])
        stock_df["stock"] = pd.to_numeric(stock_df["stock"], errors="coerce")
        stock_df["stock date"] = pd.to_datetime(stock_df["stock date"], errors="coerce")  # Convert Stock Date to datetime

        # Filter for the selected region
        filtered_df = stock_df[stock_df["region"] == region]

        # Sum total stock for the region
        total_stock = filtered_df["stock"].sum()

        # Display the total stock quantity in Streamlit
        st.metric(label=f"Total Stock in {region} ({brand})", value=f"{total_stock:,.0f} units")

        # Show summary statistics
        st.subheader(f"Stock Summary for {region} ({brand})")
        if not filtered_df.empty:
            st.write(filtered_df["stock"].describe())
        else:
            st.warning(f"No data available for {region} ({brand})")

        # Stock trend over time (by day)
        st.subheader(f"Stock Trend for {region} ({brand}) Over Time")

        # Group stock values by date
        stock_trend = filtered_df.groupby(filtered_df["stock date"].dt.date)["stock"].sum().reset_index()

        # Plot stock trend as a line chart
        plt.figure(figsize=(12, 6))
        plt.plot(stock_trend["stock date"], stock_trend["stock"], marker='o', linestyle='-', color='green')
        plt.xlabel("Date", fontsize=12)
        plt.ylabel("Stock Quantity", fontsize=12)
        plt.title(f"Stock Trend for {region} ({brand})", fontsize=16)
        plt.xticks(rotation=45)
        plt.grid(True)
        st.pyplot(plt)

    else:
        st.error("Stock dataset is missing required columns.")
