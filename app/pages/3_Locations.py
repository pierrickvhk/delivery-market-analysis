from __future__ import annotations

from pathlib import Path

import duckdb
import plotly.express as px
import streamlit as st

from delivery_market_analysis.queries import query_df

st.set_page_config(page_title="Locations", layout="wide")

st.title("Locations")
st.caption("Distribution of restaurants per city, and basic coverage mapping.")

db_path = Path("data/processed/analytics.duckdb")
con = duckdb.connect(db_path.as_posix(), read_only=True)

platforms = ["All"] + [r[0] for r in con.execute("SELECT DISTINCT platform FROM stg_restaurants ORDER BY 1;").fetchall()]
sel_platform = st.selectbox("Platform", platforms, index=0)

params = {"platform": None if sel_platform == "All" else sel_platform}

# Restaurants per city
city_counts = query_df(
    con,
    """
    SELECT
      COALESCE(NULLIF(city, ''), 'Unknown') AS city,
      platform,
      COUNT(*) AS restaurant_count
    FROM stg_restaurants
    WHERE ($platform IS NULL OR platform = $platform)
    GROUP BY 1,2
    """,
    params,
)

top = city_counts.sort_values("restaurant_count", ascending=False).head(25)
fig = px.bar(top, x="restaurant_count", y="city", color="platform" if sel_platform == "All" else None, orientation="h")
st.plotly_chart(fig, use_container_width=True)

st.divider()

# Map points (sampled to keep it fast)
points = query_df(
    con,
    """
    SELECT platform, restaurant_name, city, latitude, longitude
    FROM stg_restaurants
    WHERE latitude IS NOT NULL AND longitude IS NOT NULL
      AND ($platform IS NULL OR platform = $platform)
    QUALIFY ROW_NUMBER() OVER (PARTITION BY platform ORDER BY restaurant_name) <= 2000
    """,
    params,
)

st.subheader("Restaurant locations (sample)")
if points.empty:
    st.info("No lat/long available for the selected platform.")
else:
    st.map(points.rename(columns={"latitude": "lat", "longitude": "lon"}))

# Dead zones (basic): cities with very low coverage
st.subheader("Low coverage cities (proxy for dead zones)")
dead = (
    city_counts.groupby("city", as_index=False)["restaurant_count"]
    .sum()
    .sort_values("restaurant_count", ascending=True)
    .head(25)
)
st.dataframe(dead, use_container_width=True)
