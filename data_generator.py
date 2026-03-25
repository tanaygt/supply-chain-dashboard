"""
data_generator.py
Generates realistic synthetic supply chain data for the dashboard.
No external dataset needed — everything is created here.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

# ── Seed for reproducibility ──────────────────────────────────────────────────
np.random.seed(42)
random.seed(42)

# ── Constants ─────────────────────────────────────────────────────────────────
CATEGORIES   = ["Electronics", "Apparel", "FMCG", "Furniture", "Pharmaceuticals"]
REGIONS      = ["North", "South", "East", "West", "Central"]
ORDER_STATUS = ["Delivered", "In Transit", "Processing", "Cancelled", "Returned"]
STATUS_WEIGHTS = [0.65, 0.15, 0.10, 0.06, 0.04]

PRODUCTS = {
    "Electronics":     ["Laptop", "Smartphone", "Headphones", "Tablet", "Smartwatch"],
    "Apparel":         ["T-Shirt", "Jeans", "Jacket", "Shoes", "Cap"],
    "FMCG":            ["Shampoo", "Toothpaste", "Soap", "Detergent", "Face Wash"],
    "Furniture":       ["Office Chair", "Study Table", "Bookshelf", "Sofa", "Bed Frame"],
    "Pharmaceuticals": ["Paracetamol", "Vitamin C", "Antacid", "Cough Syrup", "Bandage"]
}

SUPPLIERS = {
    "Electronics":     ["TechSource Pvt Ltd", "DigiVendors Co.", "ElectroPro Suppliers"],
    "Apparel":         ["FabricHub India", "StyleChain Ltd", "WeaveCraft Exports"],
    "FMCG":            ["FastMove Goods", "QuickSupply Co.", "DailyNeeds Distributor"],
    "Furniture":       ["WoodCraft Ventures", "FurnishPro Logistics", "HomeBase Suppliers"],
    "Pharmaceuticals": ["MediLink Pharma", "HealthBridge Distributors", "CureCo Supply"]
}


# ── 1. INVENTORY DATA ─────────────────────────────────────────────────────────
def generate_inventory() -> pd.DataFrame:
    rows = []
    pid  = 1
    for category, products in PRODUCTS.items():
        for product in products:
            stock_level   = random.randint(10, 500)
            reorder_point = random.randint(30, 100)
            rows.append({
                "product_id":    f"P{pid:03d}",
                "product_name":  product,
                "category":      category,
                "stock_level":   stock_level,
                "reorder_point": reorder_point,
                "unit_cost":     round(random.uniform(50, 5000), 2),
                "turnover_rate": round(random.uniform(2.0, 12.0), 2),
                "warehouse":     f"WH-{random.randint(1,5)}"
            })
            pid += 1
    return pd.DataFrame(rows)


# ── 2. ORDERS DATA ────────────────────────────────────────────────────────────
def generate_orders(n: int = 500) -> pd.DataFrame:
    start_date = datetime(2024, 1, 1)
    rows = []

    all_products = [(cat, prod)
                    for cat, prods in PRODUCTS.items()
                    for prod in prods]

    for i in range(n):
        order_date     = start_date + timedelta(days=random.randint(0, 364))
        delivery_days  = random.randint(1, 15)
        delivery_date  = order_date + timedelta(days=delivery_days)
        sla_days       = 7
        status         = random.choices(ORDER_STATUS, weights=STATUS_WEIGHTS)[0]
        on_time        = 1 if delivery_days <= sla_days else 0
        category, prod = random.choice(all_products)
        qty            = random.randint(1, 50)
        unit_price     = round(random.uniform(100, 8000), 2)

        rows.append({
            "order_id":      f"ORD-{i+1:04d}",
            "order_date":    order_date,
            "delivery_date": delivery_date,
            "delivery_days": delivery_days,
            "on_time":       on_time,
            "status":        status,
            "product":       prod,
            "category":      category,
            "region":        random.choice(REGIONS),
            "quantity":      qty,
            "unit_price":    unit_price,
            "order_value":   round(qty * unit_price, 2),
            "courier":       random.choice(["BlueDart", "Delhivery", "DTDC",
                                            "Ecom Express", "XpressBees"])
        })

    df = pd.DataFrame(rows)
    df["order_date"]    = pd.to_datetime(df["order_date"])
    df["delivery_date"] = pd.to_datetime(df["delivery_date"])
    return df


# ── 3. SUPPLIER DATA ──────────────────────────────────────────────────────────
def generate_suppliers() -> pd.DataFrame:
    rows = []
    sid  = 1
    for category, supplier_list in SUPPLIERS.items():
        for supplier in supplier_list:
            rows.append({
                "supplier_id":     f"S{sid:03d}",
                "supplier_name":   supplier,
                "category":        category,
                "rating":          round(random.uniform(2.5, 5.0), 1),
                "lead_time_days":  random.randint(3, 21),
                "defect_rate":     round(random.uniform(0.5, 8.0), 2),
                "total_orders":    random.randint(50, 500),
                "contract_value":  round(random.uniform(100000, 5000000), 2),
                "payment_terms":   random.choice(["Net 30", "Net 45", "Net 60",
                                                   "Advance", "COD"]),
                "country":         random.choice(["India", "China", "USA",
                                                   "Germany", "Vietnam"])
            })
            sid += 1
    return pd.DataFrame(rows)


# ── 4. DEMAND FORECAST DATA ───────────────────────────────────────────────────
def generate_forecast() -> pd.DataFrame:
    """
    Simple Moving Average forecast:
    - 12 months of historical data
    - 3 months of forecast with ±15% confidence interval
    """
    rows = []
    all_products = [(cat, prod)
                    for cat, prods in PRODUCTS.items()
                    for prod in prods]

    for category, product in all_products:
        base_demand = random.randint(100, 1000)
        trend       = random.uniform(-5, 15)        # monthly trend (units)
        seasonality = random.uniform(0.05, 0.25)    # amplitude

        # Historical — 12 months
        hist_dates  = [datetime(2024, 1, 1) + timedelta(days=30 * i) for i in range(12)]
        hist_demand = []
        for idx, d in enumerate(hist_dates):
            seasonal_factor = 1 + seasonality * np.sin(2 * np.pi * idx / 12)
            noise           = random.gauss(0, base_demand * 0.05)
            demand          = max(0, round(base_demand + trend * idx + noise) * seasonal_factor)
            hist_demand.append(round(demand))
            rows.append({
                "product_name": product,
                "category":     category,
                "date":         d,
                "demand":       round(demand),
                "upper_bound":  None,
                "lower_bound":  None,
                "type":         "Historical"
            })

        # Moving average base for forecast
        ma_base = np.mean(hist_demand[-3:])

        # Forecast — 3 months
        for fwd in range(1, 4):
            f_date       = datetime(2024, 1, 1) + timedelta(days=30 * (12 + fwd - 1))
            seasonal_fac = 1 + seasonality * np.sin(2 * np.pi * (12 + fwd) / 12)
            f_demand     = round(ma_base * seasonal_fac + trend * fwd)
            f_demand     = max(0, f_demand)
            rows.append({
                "product_name": product,
                "category":     category,
                "date":         f_date,
                "demand":       f_demand,
                "upper_bound":  round(f_demand * 1.15),
                "lower_bound":  round(f_demand * 0.85),
                "type":         "Forecast"
            })

    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"])
    return df


# ── MASTER FUNCTION ───────────────────────────────────────────────────────────
def generate_all_data():
    inventory  = generate_inventory()
    orders     = generate_orders(500)
    suppliers  = generate_suppliers()
    forecast   = generate_forecast()
    return inventory, orders, suppliers, forecast


if __name__ == "__main__":
    inv, ord_, sup, fc = generate_all_data()
    print("✅ Inventory :", inv.shape)
    print("✅ Orders    :", ord_.shape)
    print("✅ Suppliers :", sup.shape)
    print("✅ Forecast  :", fc.shape)

    # Save to CSV (optional — for Excel/Power BI use)
    inv.to_csv("data/inventory.csv",  index=False)
    ord_.to_csv("data/orders.csv",    index=False)
    sup.to_csv("data/suppliers.csv",  index=False)
    fc.to_csv("data/forecast.csv",    index=False)
    print("✅ CSVs saved to /data folder")
