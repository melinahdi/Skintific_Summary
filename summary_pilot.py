import streamlit as st
import pandas as pd

# Load data
@st.cache_data
def load_data():
    file_skt_stock = "[SKT & G2G] - Master Stock MTD - [SKT] - Stock.csv"
    file_g2g_stock = "[SKT & G2G] - Master Stock MTD - [G2G] - Stock.csv"
    file_sales = "Chatbot Pilot - Extract 1.csv"
    
    df_skt = pd.read_csv(file_skt_stock)
    df_g2g = pd.read_csv(file_g2g_stock)
    df_sales = pd.read_csv(file_sales)
    
    # Clean up column names
    df_skt.columns = df_skt.columns.str.strip()
    df_g2g.columns = df_g2g.columns.str.strip()
    df_sales.columns = df_sales.columns.str.strip()
    
    return df_skt, df_g2g, df_sales

# Load datasets
df_skt, df_g2g, df_sales = load_data()

# Rename Category column to brand
df_skt.rename(columns={"Category": "brand", "Distributor": "Distributor"}, inplace=True)
df_g2g.rename(columns={"Category": "brand", "Distributor": "Distributor"}, inplace=True)
df_sales.rename(columns={"WorkplaceName": "Distributor"}, inplace=True)

# Ensure distributor names are capitalized consistently (ALL CAPS)
df_skt["Distributor"] = df_skt["Distributor"].str.upper()
df_g2g["Distributor"] = df_g2g["Distributor"].str.upper()
df_sales["Distributor"] = df_sales["Distributor"].str.upper()

# Filter stock data where brand is SKINTIFIC or G2G
df_skt = df_skt[df_skt["brand"] == "SKINTIFIC"]
df_g2g = df_g2g[df_g2g["brand"] == "G2G"]

# Prepare stock data
df_stock = pd.concat([df_skt[["Distributor", "Stock", "brand", "Region", "Max Mapping"]], 
                      df_g2g[["Distributor", "Stock", "brand", "Region", "Max Mapping"]]])

df_stock["Stock"] = df_stock["Stock"].astype(str).str.replace(",", "").astype(float)

# Filter stock data based on Max Mapping (latest data), where Max Mapping is not null
df_stock = df_stock[df_stock["Max Mapping"].notna()]

# Aggregate sales data by Distributor, brand, Region
df_sales_filtered = df_sales[["brand", "NettAmountIncTax", "region", "Distributor"]].groupby(["brand", "region", "Distributor"]).sum().reset_index()

# Standardize 'region' column in df_sales_filtered to match df_stock
df_sales_filtered["region"] = df_sales_filtered["region"].str.title()

# Merge stock and sales data by Distributor
df_merged = df_stock.merge(df_sales_filtered, left_on=["brand", "Region", "Distributor"], 
                           right_on=["brand", "region", "Distributor"], how="left")

# Aggregate stock and sales by Distributor, Brand, Region
df_aggregated = df_merged.groupby(["Distributor", "brand", "Region"], as_index=False).agg({
    "Stock": "sum",
    "NettAmountIncTax": "mean"
})

# Calculate Stock-to-Sales Ratio
df_aggregated["Stock_to_Sales_Ratio"] = df_aggregated["Stock"] / (df_aggregated["NettAmountIncTax"])

# Streamlit UI
st.title("Dead Stock Analysis")

# Filters
region_options = ["All"] + sorted(df_aggregated["Region"].dropna().unique().tolist())
brand_options = ["All"] + sorted(df_aggregated["brand"].unique().tolist())
selected_region = st.selectbox("Select Region", region_options)
selected_brand = st.selectbox("Select Brand", brand_options)

# Apply filters
filtered_df = df_aggregated.copy()
if selected_region != "All":
    filtered_df = filtered_df[filtered_df["Region"] == selected_region]
if selected_brand != "All":
    filtered_df = filtered_df[filtered_df["brand"] == selected_brand]

# Identify dead stock
dead_stock_df = filtered_df[filtered_df["Stock_to_Sales_Ratio"] < 6]

# Display results
if not dead_stock_df.empty:
    st.write("### Dead Stock")
    st.dataframe(dead_stock_df[["Distributor", "Stock", "brand", "Region", "Stock_to_Sales_Ratio"]])
    
    # Generate summary with Stock-to-Sales Ratio in brackets and brand outside
    dead_stock_summary = ", ".join(
        dead_stock_df.apply(lambda row: f"{row['Distributor']} ({row['Stock_to_Sales_Ratio']:.8f}) - {row['brand']}", axis=1)
    )
    
    st.write(f"Distributor dengan kondisi dead stock adalah: {dead_stock_summary}")
else:
    st.write("No dead stock found based on the given criteria.")
