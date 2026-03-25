"""
Supply Chain Analytics Dashboard
Author: Tanay Shrivastava
Description: Interactive dashboard for supply chain KPIs, inventory tracking,
             supplier performance, and demand forecasting.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from data_generator import generate_all_data

st.set_page_config(
    page_title="Supply Chain Analytics Dashboard",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .stMetric { background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 8px; padding: 10px; }
    h1 { color: #2c3e50; }
    h2 { color: #34495e; }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    return generate_all_data()

inventory_df, orders_df, suppliers_df, forecast_df = load_data()

st.sidebar.image("https://img.icons8.com/color/96/supply-chain.png", width=80)
st.sidebar.title("🔍 Filters")

min_date = orders_df["order_date"].min()
max_date = orders_df["order_date"].max()
date_range = st.sidebar.date_input("Select Date Range", value=(min_date, max_date), min_value=min_date, max_value=max_date)

categories = ["All"] + sorted(inventory_df["category"].unique().tolist())
selected_category = st.sidebar.selectbox("Product Category", categories)

suppliers = ["All"] + sorted(suppliers_df["supplier_name"].unique().tolist())
selected_supplier = st.sidebar.selectbox("Supplier", suppliers)

if len(date_range) == 2:
    filtered_orders = orders_df[
        (orders_df["order_date"] >= pd.to_datetime(date_range[0])) &
        (orders_df["order_date"] <= pd.to_datetime(date_range[1]))
    ]
else:
    filtered_orders = orders_df.copy()

filtered_inventory = inventory_df.copy()
if selected_category != "All":
    filtered_inventory = filtered_inventory[filtered_inventory["category"] == selected_category]

filtered_suppliers = suppliers_df.copy()
if selected_supplier != "All":
    filtered_suppliers = filtered_suppliers[filtered_suppliers["supplier_name"] == selected_supplier]

st.title("📦 Supply Chain Analytics Dashboard")
st.markdown("**Real-time visibility into inventory, orders, supplier performance & demand forecasting**")
st.markdown("---")

st.subheader("📊 Key Performance Indicators")
col1, col2, col3, col4, col5 = st.columns(5)

total_orders        = len(filtered_orders)
fulfilled_orders    = len(filtered_orders[filtered_orders["status"] == "Delivered"])
fulfillment_rate    = round((fulfilled_orders / total_orders) * 100, 1) if total_orders > 0 else 0
avg_delivery_days   = round(filtered_orders["delivery_days"].mean(), 1)
low_stock_items     = len(filtered_inventory[filtered_inventory["stock_level"] < filtered_inventory["reorder_point"]])
avg_supplier_rating = round(filtered_suppliers["rating"].mean(), 2)

col1.metric("📦 Total Orders",      f"{total_orders:,}")
col2.metric("✅ Fulfillment Rate",  f"{fulfillment_rate}%",  delta=f"{fulfillment_rate - 85:.1f}% vs target")
col3.metric("🚚 Avg Delivery Days", f"{avg_delivery_days}d", delta=f"{-(avg_delivery_days - 5):.1f}d vs SLA", delta_color="inverse")
col4.metric("⚠️ Low Stock Items",   f"{low_stock_items}",    delta="Needs reorder" if low_stock_items > 0 else "All good", delta_color="inverse")
col5.metric("⭐ Supplier Rating",   f"{avg_supplier_rating}/5")
st.markdown("---")

st.subheader("🏭 Inventory Analysis")
col_left, col_right = st.columns(2)

with col_left:
    category_stock = filtered_inventory.groupby("category")["stock_level"].sum().reset_index()
    fig_stock = px.bar(category_stock, x="category", y="stock_level",
        title="Current Stock Levels by Category", color="stock_level",
        color_continuous_scale="Blues", labels={"stock_level": "Units in Stock", "category": "Category"})
    fig_stock.update_layout(showlegend=False, height=350)
    st.plotly_chart(fig_stock, use_container_width=True)

with col_right:
    low_stock_df = filtered_inventory[filtered_inventory["stock_level"] < filtered_inventory["reorder_point"]].copy()
    low_stock_df = low_stock_df.sort_values("stock_level").head(10)
    if not low_stock_df.empty:
        fig_reorder = go.Figure()
        fig_reorder.add_trace(go.Bar(name="Current Stock", x=low_stock_df["product_name"], y=low_stock_df["stock_level"], marker_color="#e74c3c"))
        fig_reorder.add_trace(go.Bar(name="Reorder Point", x=low_stock_df["product_name"], y=low_stock_df["reorder_point"], marker_color="#3498db", opacity=0.5))
        fig_reorder.update_layout(title="⚠️ Items Below Reorder Point", barmode="overlay", height=350, xaxis_tickangle=-30)
        st.plotly_chart(fig_reorder, use_container_width=True)
    else:
        st.success("✅ All items are above reorder point!")

st.markdown("**📋 Inventory Turnover Report**")
turnover_df = filtered_inventory[["product_name","category","stock_level","reorder_point","unit_cost","turnover_rate"]].copy()
turnover_df["stock_value"] = (turnover_df["stock_level"] * turnover_df["unit_cost"]).round(2)
turnover_df["status"] = turnover_df.apply(lambda r: "🔴 Low" if r["stock_level"] < r["reorder_point"] else "🟢 OK", axis=1)
turnover_df = turnover_df.rename(columns={"product_name":"Product","category":"Category","stock_level":"Stock","reorder_point":"Reorder Pt","unit_cost":"Unit Cost (₹)","turnover_rate":"Turnover Rate","stock_value":"Stock Value (₹)","status":"Status"})
st.dataframe(turnover_df, use_container_width=True, height=250)
st.markdown("---")

st.subheader("🚚 Order & Logistics Analysis")
col1, col2 = st.columns(2)

with col1:
    orders_by_month = filtered_orders.copy()
    orders_by_month["month"] = orders_by_month["order_date"].dt.to_period("M").astype(str)
    monthly = orders_by_month.groupby("month").agg(total_orders=("order_id","count"), revenue=("order_value","sum")).reset_index()
    fig_monthly = make_subplots(specs=[[{"secondary_y": True}]])
    fig_monthly.add_trace(go.Bar(x=monthly["month"], y=monthly["total_orders"], name="Orders", marker_color="#3498db"), secondary_y=False)
    fig_monthly.add_trace(go.Scatter(x=monthly["month"], y=monthly["revenue"], name="Revenue (₹)", mode="lines+markers", line=dict(color="#e74c3c", width=2)), secondary_y=True)
    fig_monthly.update_layout(title="Monthly Orders & Revenue", height=350)
    fig_monthly.update_yaxes(title_text="No. of Orders", secondary_y=False)
    fig_monthly.update_yaxes(title_text="Revenue (₹)", secondary_y=True)
    st.plotly_chart(fig_monthly, use_container_width=True)

with col2:
    status_counts = filtered_orders["status"].value_counts().reset_index()
    status_counts.columns = ["Status", "Count"]
    color_map = {"Delivered":"#2ecc71","In Transit":"#f39c12","Processing":"#3498db","Cancelled":"#e74c3c","Returned":"#9b59b6"}
    fig_status = px.pie(status_counts, names="Status", values="Count", title="Order Status Distribution", color="Status", color_discrete_map=color_map, hole=0.4)
    fig_status.update_layout(height=350)
    st.plotly_chart(fig_status, use_container_width=True)

st.markdown("**🗺️ Delivery Performance by Region**")
region_perf = filtered_orders.groupby("region").agg(avg_delivery_days=("delivery_days","mean"), orders=("order_id","count"), on_time_pct=("on_time","mean")).reset_index()
region_perf["avg_delivery_days"] = region_perf["avg_delivery_days"].round(1)
region_perf["on_time_pct"] = (region_perf["on_time_pct"] * 100).round(1)
fig_region = px.scatter(region_perf, x="avg_delivery_days", y="on_time_pct", size="orders", color="region",
    title="Delivery Days vs On-Time % by Region (bubble = order volume)",
    labels={"avg_delivery_days":"Avg Delivery Days","on_time_pct":"On-Time Delivery %","region":"Region"})
fig_region.add_hline(y=90, line_dash="dash", line_color="red", annotation_text="90% SLA Target")
fig_region.update_layout(height=350)
st.plotly_chart(fig_region, use_container_width=True)
st.markdown("---")

st.subheader("🤝 Supplier Performance Scorecard")
col1, col2 = st.columns(2)

with col1:
    fig_supplier = px.bar(filtered_suppliers.sort_values("rating", ascending=True), x="rating", y="supplier_name",
        orientation="h", color="rating", color_continuous_scale="RdYlGn", title="Supplier Ratings",
        labels={"rating":"Rating (out of 5)","supplier_name":"Supplier"})
    fig_supplier.update_layout(height=400, showlegend=False)
    st.plotly_chart(fig_supplier, use_container_width=True)

with col2:
    fig_lead = px.scatter(filtered_suppliers, x="lead_time_days", y="defect_rate", color="rating",
        size="total_orders", hover_name="supplier_name", title="Lead Time vs Defect Rate (color = rating)",
        labels={"lead_time_days":"Lead Time (Days)","defect_rate":"Defect Rate (%)","rating":"Rating"},
        color_continuous_scale="RdYlGn")
    fig_lead.update_layout(height=400)
    st.plotly_chart(fig_lead, use_container_width=True)

st.markdown("**📋 Supplier Summary Table**")
supplier_display = filtered_suppliers[["supplier_name","category","rating","lead_time_days","defect_rate","total_orders","contract_value"]].copy()
supplier_display["contract_value"] = supplier_display["contract_value"].apply(lambda x: f"₹{x:,.0f}")
supplier_display["defect_rate"]    = supplier_display["defect_rate"].apply(lambda x: f"{x:.1f}%")
supplier_display.columns = ["Supplier","Category","Rating","Lead Time (Days)","Defect Rate","Total Orders","Contract Value"]
st.dataframe(supplier_display, use_container_width=True)
st.markdown("---")

st.subheader("📈 Demand Forecasting (3-Month Outlook)")
selected_product = st.selectbox("Select Product to Forecast", forecast_df["product_name"].unique())

prod_forecast = forecast_df[forecast_df["product_name"] == selected_product].copy()
hist = prod_forecast[prod_forecast["type"] == "Historical"].copy()
fore = prod_forecast[prod_forecast["type"] == "Forecast"].copy()

fig_forecast = go.Figure()

fig_forecast.add_trace(go.Scatter(
    x=hist["date"], y=hist["demand"], name="Historical Demand",
    mode="lines+markers", line=dict(color="#3498db", width=2)
))

fig_forecast.add_trace(go.Scatter(
    x=fore["date"], y=fore["demand"], name="Forecasted Demand",
    mode="lines+markers", line=dict(color="#e74c3c", width=2, dash="dash")
))

fig_forecast.add_trace(go.Scatter(
    x=pd.concat([fore["date"], fore["date"][::-1]]),
    y=pd.concat([fore["upper_bound"], fore["lower_bound"][::-1]]),
    fill="toself", fillcolor="rgba(231,76,60,0.1)",
    line=dict(color="rgba(255,255,255,0)"), name="Confidence Interval"
))

# ── FIXED: vertical line using scatter trace instead of add_vline ─────────────
forecast_start = hist["date"].max()
y_max = float(prod_forecast["demand"].max()) * 1.15
fig_forecast.add_trace(go.Scatter(
    x=[forecast_start, forecast_start],
    y=[0, y_max],
    mode="lines",
    line=dict(color="gray", width=1, dash="dot"),
    name="Forecast Start"
))
# ─────────────────────────────────────────────────────────────────────────────

fig_forecast.update_layout(
    title=f"Demand Forecast — {selected_product}",
    xaxis_title="Date", yaxis_title="Units Demanded",
    height=400, hovermode="x unified"
)
st.plotly_chart(fig_forecast, use_container_width=True)

col1, col2, col3 = st.columns(3)
avg_hist     = hist["demand"].mean()
avg_forecast = fore["demand"].mean()
pct_change   = ((avg_forecast - avg_hist) / avg_hist) * 100
col1.metric("📊 Avg Historical Demand", f"{avg_hist:.0f} units/month")
col2.metric("🔮 Avg Forecasted Demand", f"{avg_forecast:.0f} units/month")
col3.metric("📈 Demand Change", f"{pct_change:+.1f}%", delta_color="normal" if pct_change > 0 else "inverse")

st.markdown("---")
st.markdown("""
<div style='text-align:center; color:#7f8c8d; font-size:13px; padding-top:10px'>
    📦 Supply Chain Analytics Dashboard &nbsp;|&nbsp; Built by <b>Tanay Shrivastava</b>
    &nbsp;|&nbsp; <a href='https://linkedin.com/in/tanayshrivastava-cse'>LinkedIn</a>
    &nbsp;|&nbsp; <a href='https://github.com/tanaygt'>GitHub</a>
</div>
""", unsafe_allow_html=True)