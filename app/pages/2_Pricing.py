from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd
import plotly.express as px
import streamlit as st

from delivery_market_analysis.queries import Filters, query_df

st.set_page_config(page_title="Pricing", layout="wide")

st.title("Pricing")
st.caption("Price distribution of menu items across platforms.")

db_path = Path("data/processed/analytics.duckdb")
con = duckdb.connect(db_path.as_posix(), read_only=True)

# Filters
platforms = ["All"] + [r[0] for r in con.execute("SELECT DISTINCT platform FROM stg_menu_items ORDER BY 1;").fetchall()]
sel_platform = st.selectbox("Platform", platforms, index=0)

filters = Filters(platform=None if sel_platform == "All" else sel_platform)

# Basic cleaning: ignore null/zero/negative prices
df = query_df(
    con,
    """
    SELECT platform, price
    FROM stg_menu_items
    WHERE price IS NOT NULL AND price > 0 AND price < 500
      AND ($platform IS NULL OR platform = $platform)
    """,
    {"platform": filters.platform},
)

if df.empty:
    st.warning("No price data available for the selected filters.")
    st.stop()

c1, c2, c3 = st.columns(3)
c1.metric("Items (filtered)", f"{len(df):,}".replace(",", " "))
c2.metric("Median price", f"{df['price'].median():.2f}")
c3.metric("Avg price", f"{df['price'].mean():.2f}")

st.divider()

# Histogram
fig = px.histogram(df, x="price", nbins=60, color="platform" if sel_platform == "All" else None)
st.plotly_chart(fig, use_container_width=True)

# Price bands table
bands = pd.cut(df["price"], bins=[0, 5, 10, 15, 20, 30, 50, 100, 500], right=True)
band_df = (
    df.assign(price_band=bands.astype(str))
      .groupby(["platform", "price_band"], dropna=False)
      .size()
      .reset_index(name="count")
      .sort_values(["platform", "count"], ascending=[True, False])
)
st.subheader("Price bands")
st.dataframe(band_df, use_container_width=True)
