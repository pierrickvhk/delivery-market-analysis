from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Late night", layout="wide")

st.title("Late night availability")
st.caption("Open-late proxy using UberEats hours data (end_time stored as minutes since midnight).")

db_path = Path("data/processed/analytics.duckdb")
con = duckdb.connect(db_path.as_posix(), read_only=True)

# Check if hours table exists
exists = (
    con.execute(
        """
        SELECT COUNT(*) FROM information_schema.tables
        WHERE table_schema='ubereats' AND table_name='restaurant_hours_to_section_hours';
        """
    ).fetchone()[0]
    > 0
)

if not exists:
    st.info("Hours table not available in ubereats schema for this dataset.")
    st.stop()

late_threshold = st.selectbox("Open-late threshold", ["21:00:00", "22:00:00", "23:00:00"], index=1)
city_filter = st.text_input("City filter (optional)", value="").strip()

params = {"city": city_filter, "threshold": late_threshold}

# Hours CTE: end_time is integer minutes since midnight (e.g., 1320 -> 22:00)
hours_cte = """
WITH hours AS (
  SELECT
    CAST(restaurant_id AS VARCHAR) AS restaurant_key,
    MAX(
      COALESCE(
        CASE
          WHEN TRY_CAST(end_time AS INTEGER) IS NOT NULL THEN
            MAKE_TIME(
              FLOOR(TRY_CAST(end_time AS INTEGER) / 60)::INTEGER,
              (TRY_CAST(end_time AS INTEGER) % 60)::INTEGER,
              0
            )
          ELSE NULL
        END
      )
    ) AS latest_end
  FROM ubereats.restaurant_hours_to_section_hours
  GROUP BY 1
)
"""

st.subheader("Restaurants and latest closing time (UberEats)")

df = con.execute(
    hours_cte
    + """
SELECT
  r.restaurant_name,
  COALESCE(NULLIF(r.city,''),'Unknown') AS city,
  r.latitude,
  r.longitude,
  h.latest_end,
  CASE WHEN h.latest_end >= CAST($threshold AS TIME) THEN 1 ELSE 0 END AS is_open_late
FROM stg_restaurants r
JOIN hours h
  ON r.platform='ubereats' AND r.restaurant_key=h.restaurant_key
WHERE ($city = '' OR LOWER(r.city) = LOWER($city))
ORDER BY is_open_late DESC, latest_end DESC NULLS LAST
LIMIT 2000;
""",
    params,
).df()

st.dataframe(df.head(200), use_container_width=True)

st.divider()
st.subheader("Open late counts by city")

counts = con.execute(
    hours_cte
    + """
SELECT
  COALESCE(NULLIF(r.city,''),'Unknown') AS city,
  SUM(CASE WHEN h.latest_end >= CAST($threshold AS TIME) THEN 1 ELSE 0 END) AS open_late,
  COUNT(*) AS total
FROM stg_restaurants r
JOIN hours h
  ON r.platform='ubereats' AND r.restaurant_key=h.restaurant_key
GROUP BY 1
ORDER BY open_late DESC
LIMIT 30;
""",
    {"threshold": late_threshold},
).df()

st.dataframe(counts, use_container_width=True)

st.divider()

open_late = df[df["is_open_late"] == 1].copy()
open_late["latitude"] = pd.to_numeric(open_late["latitude"], errors="coerce")
open_late["longitude"] = pd.to_numeric(open_late["longitude"], errors="coerce")
open_late = open_late.dropna(subset=["latitude", "longitude"])

if open_late.empty:
    st.info("No mappable open-late restaurants (missing coordinates or none match the threshold).")
else:
    st.subheader("Map (open late only)")
    st.map(open_late.rename(columns={"latitude": "lat", "longitude": "lon"})[["lat", "lon"]])
