from __future__ import annotations

from pathlib import Path

import duckdb
import streamlit as st

st.set_page_config(page_title="Cross-platform", layout="wide")
st.title("Cross-platform")
st.caption("WHO: top hummus restaurants and platform comparisons where available.")

db_path = Path("data/processed/analytics.duckdb")
con = duckdb.connect(db_path.as_posix(), read_only=True)

platforms = ["All"] + [r[0] for r in con.execute("SELECT DISTINCT platform FROM stg_restaurants ORDER BY 1;").fetchall()]
sel_platform = st.selectbox("Platform", platforms, index=0)
params = {"platform": None if sel_platform == "All" else sel_platform}

st.subheader("WHO: Top 3 hummus serving restaurants")
hummus = con.execute(
    """
    WITH hummus_items AS (
      SELECT platform, restaurant_key, price
      FROM vw_item_search
      WHERE LOWER(item_name) LIKE '%hummus%' OR LOWER(COALESCE(description,'')) LIKE '%hummus%'
    ),
    agg AS (
      SELECT platform, restaurant_key,
             COUNT(*) AS hummus_items,
             AVG(price) AS avg_hummus_price
      FROM hummus_items
      GROUP BY 1,2
    )
    SELECT
      r.platform,
      r.restaurant_name,
      r.city,
      a.hummus_items,
      ROUND(a.avg_hummus_price, 2) AS avg_hummus_price,
      r.rating_value,
      r.rating_count
    FROM agg a
    JOIN stg_restaurants r
      ON r.platform = a.platform AND r.restaurant_key = a.restaurant_key
    WHERE ($platform IS NULL OR r.platform = $platform)
    ORDER BY a.hummus_items DESC, r.rating_value DESC NULLS LAST, r.rating_count DESC NULLS LAST
    LIMIT 3;
    """,
    params,
).df()
st.dataframe(hummus, use_container_width=True)

st.divider()

st.subheader("Delivery fees by platform (where available)")
fees = con.execute(
    """
    SELECT platform,
           COUNT(*) AS n_restaurants,
           ROUND(AVG(delivery_fee), 2) AS avg_delivery_fee,
           ROUND(MEDIAN(delivery_fee), 2) AS median_delivery_fee
    FROM stg_restaurants
    WHERE delivery_fee IS NOT NULL
      AND ($platform IS NULL OR platform = $platform)
    GROUP BY 1
    ORDER BY 1;
    """,
    params,
).df()
st.dataframe(fees, use_container_width=True)

st.divider()

st.subheader("Rating distribution by platform")
ratings = con.execute(
    """
    SELECT platform,
           COUNT(*) AS n_restaurants,
           ROUND(AVG(rating_value), 2) AS avg_rating,
           ROUND(MEDIAN(rating_value), 2) AS median_rating
    FROM stg_restaurants
    WHERE rating_value IS NOT NULL
      AND ($platform IS NULL OR platform = $platform)
    GROUP BY 1
    ORDER BY 1;
    """,
    params,
).df()
st.dataframe(ratings, use_container_width=True)
