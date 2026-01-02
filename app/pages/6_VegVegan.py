from __future__ import annotations

from pathlib import Path

import duckdb
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Veg/Vegan", layout="wide")
st.title("Veg/Vegan")
st.caption("How vegetarian and vegan availability varies by area (heuristic from item names/descriptions).")

db_path = Path("data/processed/analytics.duckdb")
con = duckdb.connect(db_path.as_posix(), read_only=True)

platforms = ["All"] + [r[0] for r in con.execute("SELECT DISTINCT platform FROM stg_restaurants ORDER BY 1;").fetchall()]
sel_platform = st.selectbox("Platform", platforms, index=0)
params = {"platform": None if sel_platform == "All" else sel_platform}

# Per city distribution
df = con.execute(
    """
    WITH tagged AS (
      SELECT platform, restaurant_key, diet_tag
      FROM vw_veg_vegan_items
      WHERE diet_tag IS NOT NULL
    ),
    per_restaurant AS (
      SELECT platform, restaurant_key,
             MAX(CASE WHEN diet_tag = 'vegan' THEN 1 ELSE 0 END) AS has_vegan,
             MAX(CASE WHEN diet_tag = 'vegetarian' THEN 1 ELSE 0 END) AS has_vegetarian
      FROM tagged
      GROUP BY 1,2
    )
    SELECT
      COALESCE(NULLIF(r.city,''),'Unknown') AS city,
      r.platform,
      COUNT(*) AS restaurants_total,
      SUM(COALESCE(p.has_vegetarian,0)) AS restaurants_with_vegetarian,
      SUM(COALESCE(p.has_vegan,0)) AS restaurants_with_vegan
    FROM stg_restaurants r
    LEFT JOIN per_restaurant p
      ON p.platform = r.platform AND p.restaurant_key = r.restaurant_key
    WHERE ($platform IS NULL OR r.platform = $platform)
    GROUP BY 1,2
    """,
    params,
).df()

if df.empty:
    st.info("No data available.")
    st.stop()

# Ratios
df["veg_ratio"] = (df["restaurants_with_vegetarian"] / df["restaurants_total"]).fillna(0)
df["vegan_ratio"] = (df["restaurants_with_vegan"] / df["restaurants_total"]).fillna(0)

top = df.sort_values("restaurants_total", ascending=False).head(25)

c1, c2 = st.columns(2)
fig1 = px.bar(top, x="veg_ratio", y="city", color="platform" if sel_platform == "All" else None, orientation="h")
fig2 = px.bar(top, x="vegan_ratio", y="city", color="platform" if sel_platform == "All" else None, orientation="h")
c1.plotly_chart(fig1, use_container_width=True)
c2.plotly_chart(fig2, use_container_width=True)

st.subheader("Table (top cities by volume)")
show = top[["platform", "city", "restaurants_total", "restaurants_with_vegetarian", "restaurants_with_vegan", "veg_ratio", "vegan_ratio"]]
st.dataframe(show, use_container_width=True)
