from __future__ import annotations

from pathlib import Path

import duckdb
import streamlit as st

st.set_page_config(page_title="Geo", layout="wide")
st.title("Geo")
st.caption("Kapsalon availability, average price mapping, and basic dead zone analysis.")

db_path = Path("data/processed/analytics.duckdb")
con = duckdb.connect(db_path.as_posix(), read_only=True)

platforms = ["All"] + [r[0] for r in con.execute("SELECT DISTINCT platform FROM stg_restaurants ORDER BY 1;").fetchall()]
sel_platform = st.selectbox("Platform", platforms, index=0)

dish = st.text_input("Dish keyword", value="kapsalon")
params = {"platform": None if sel_platform == "All" else sel_platform, "dish": f"%{dish.lower()}%"}

st.subheader("Locations offering the dish and average price")

kaps = con.execute(
    """
    WITH dish_items AS (
      SELECT platform, restaurant_key, price
      FROM vw_item_search
      WHERE LOWER(item_name) LIKE $dish OR LOWER(COALESCE(description,'')) LIKE $dish
    ),
    avg_price AS (
      SELECT platform, restaurant_key, AVG(price) AS avg_dish_price, COUNT(*) AS matched_items
      FROM dish_items
      GROUP BY 1,2
    )
    SELECT
      r.platform,
      r.restaurant_name,
      r.city,
      r.postal_code,
      r.latitude,
      r.longitude,
      a.avg_dish_price,
      a.matched_items
    FROM stg_restaurants r
    JOIN avg_price a
      ON a.platform = r.platform AND a.restaurant_key = r.restaurant_key
    WHERE r.latitude IS NOT NULL AND r.longitude IS NOT NULL
      AND ($platform IS NULL OR r.platform = $platform)
    ORDER BY a.matched_items DESC, a.avg_dish_price ASC
    LIMIT 2000;
    """,
    params,
).df()

if kaps.empty:
    st.info("No matches found. Try another keyword (e.g., 'hummus', 'falafel').")
    st.stop()

kaps["avg_dish_price"] = kaps["avg_dish_price"].round(2)
st.dataframe(kaps.head(50), use_container_width=True)

st.divider()

st.subheader("Map (sample)")
map_df = kaps.rename(columns={"latitude": "lat", "longitude": "lon"})
st.map(map_df[["lat", "lon"]])

st.divider()

st.subheader("Dead zones (proxy)")
st.caption("Proxy: cities with very low restaurant counts (based on available city field).")

dead = con.execute(
    """
    SELECT COALESCE(NULLIF(city,''),'Unknown') AS city, COUNT(*) AS restaurant_count
    FROM stg_restaurants
    WHERE ($platform IS NULL OR platform = $platform)
    GROUP BY 1
    ORDER BY restaurant_count ASC
    LIMIT 30;
    """,
    {"platform": params["platform"]},
).df()

st.dataframe(dead, use_container_width=True)
