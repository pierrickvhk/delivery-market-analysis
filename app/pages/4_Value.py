from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Value", layout="wide")
st.title("Value")
st.caption("Top pizza restaurants by rating and best price-to-rating ratio.")

db_path = Path("data/processed/analytics.duckdb")
con = duckdb.connect(db_path.as_posix(), read_only=True)

platforms = ["All"] + [r[0] for r in con.execute("SELECT DISTINCT platform FROM stg_restaurants ORDER BY 1;").fetchall()]
sel_platform = st.selectbox("Platform", platforms, index=0)

min_reviews = st.slider("Minimum review count", min_value=0, max_value=200, value=20, step=5)

params = {"platform": None if sel_platform == "All" else sel_platform, "min_reviews": min_reviews}

st.subheader("Top 10 pizza restaurants by rating")
pizza = con.execute(
    """
    SELECT platform, restaurant_name, city, rating_value, rating_count
    FROM vw_pizza_restaurants
    WHERE rating_value IS NOT NULL
      AND rating_count IS NOT NULL
      AND rating_count >= $min_reviews
      AND ($platform IS NULL OR platform = $platform)
    ORDER BY rating_value DESC, rating_count DESC
    LIMIT 10;
    """,
    params,
).df()

st.dataframe(pizza, use_container_width=True)

st.divider()

st.subheader("Best price-to-rating ratio (proxy)")
st.caption("Proxy: compare restaurant rating vs median menu item price (lower price, higher rating).")

value = con.execute(
    """
    WITH price_per_restaurant AS (
      SELECT platform, restaurant_key, MEDIAN(price) AS median_price
      FROM vw_item_search
      GROUP BY 1,2
    )
    SELECT
      r.platform,
      r.restaurant_name,
      r.city,
      r.rating_value,
      r.rating_count,
      p.median_price,
      (r.rating_value / NULLIF(p.median_price, 0)) AS value_score
    FROM stg_restaurants r
    JOIN price_per_restaurant p
      ON p.platform = r.platform AND p.restaurant_key = r.restaurant_key
    WHERE r.rating_value IS NOT NULL
      AND p.median_price IS NOT NULL
      AND r.rating_count IS NOT NULL
      AND r.rating_count >= $min_reviews
      AND ($platform IS NULL OR r.platform = $platform)
    ORDER BY value_score DESC
    LIMIT 25;
    """,
    params,
).df()

# Clean display
if not value.empty:
    value["median_price"] = value["median_price"].round(2)
    value["value_score"] = value["value_score"].round(3)

st.dataframe(value, use_container_width=True)

if not value.empty:
    fig = px.scatter(
        value,
        x="median_price",
        y="rating_value",
        size="rating_count",
        hover_name="restaurant_name",
        color="platform" if sel_platform == "All" else None,
    )
    st.plotly_chart(fig, use_container_width=True)
