"""
Generate a sample sales dataset for testing.
Run: python generate_sample.py
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

np.random.seed(42)
n = 1000

dates     = [datetime(2024, 1, 1) + timedelta(days=i % 365) for i in range(n)]
products  = np.random.choice(["Laptop", "Mouse", "Keyboard", "Monitor", "USB Cable", "Webcam"], n)
categories= np.where(np.isin(products, ["Laptop", "Monitor"]), "Electronics",
            np.where(np.isin(products, ["Mouse", "Keyboard"]), "Accessories", "Accessories"))
regions   = np.random.choice(["Jakarta", "Bandung", "Surabaya", "Medan", "Makassar"], n)
sales     = np.random.lognormal(mean=10, sigma=1.2, size=n).round(0)
quantity  = np.random.randint(1, 20, n)
discount  = np.random.choice([0, 0.05, 0.10, 0.15, 0.20], n)
profit    = (sales * (1 - discount) * 0.3).round(0)

# Add some missing values
idx_miss = np.random.choice(n, 30, replace=False)
sales_arr = sales.astype(float)
sales_arr[idx_miss[:10]] = np.nan

df = pd.DataFrame({
    "Date"    : dates,
    "Product" : products,
    "Category": categories,
    "Region"  : regions,
    "Sales"   : sales_arr,
    "Quantity": quantity,
    "Discount": discount,
    "Profit"  : profit,
})

out = os.path.join(os.path.dirname(__file__), "data", "sample_dataset", "sales_data.xlsx")
os.makedirs(os.path.dirname(out), exist_ok=True)
df.to_excel(out, index=False)
print(f"✅ Sample dataset saved: {out}  ({len(df)} rows)")
