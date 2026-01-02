from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Cross-platform", layout="wide")

st.title("Cross-platform overlap (G1)")
st.caption(
    "Restaurant entity resolution across platforms. Quantifies overlap and highlights cross-platform opportunities."
)

DB_PATH = Path("data/processed/analytics.duckdb")
con = duckdb.connect(DB_PATH.as_posix(), read_only=True)

# Guard: matching must exist
has_matches = con.execute(
    """
    SELECT COUNT(*) > 0
    FROM information_schema.tables
    WHERE table_name = 'g1_restaurant_matches';
    """
).fetchone()[0]

if not has_matches:
    st.error("G1 matching not built. Run: python -m delivery_market_analysis.matching")
    st.stop()

# ---------------------------------------------------------------------
# KPIs: overall overlap distribution
dist = con.execute(
    """
    SELECT platform_count, COUNT(*) AS n
    FROM vw_canonical_restaurants
    GROUP BY 1
    ORDER BY 1;
    """
).df()

total = int(dist["n"].sum()) if not dist.empty else 0
single = int(dist.loc[dist["platform_count"] == 1, "n"].sum()) if total else 0
cross = total - single
cross_share = (cross / total) if total else 0.0

c1, c2, c3, c4 = st.columns(4)
c1.metric("Canonical restaurants", f"{total:,}")
c2.metric("Cross-platform (2+)", f"{cross:,}")
c3.metric("Cross-platform share", f"{cross_share:.1%}")
c4.metric("Platforms", "3")

st.divider()

st.subheader("Overlap distribution")
fig = px.bar(dist, x="platform_count", y="n", labels={"platform_count": "Platforms per restaurant", "n": "Count"})
st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------------------
# Pairwise overlap matrix (deliveroo/takeaway/ubereats)
st.subheader("Pairwise overlap")
pairs = con.execute(
    """
    WITH canon_platforms AS (
      SELECT canonical_id, platform
      FROM g1_restaurant_matches
      GROUP BY 1,2
    ),
    pair AS (
      SELECT
        a.platform AS p1,
        b.platform AS p2,
        COUNT(DISTINCT a.canonical_id) AS overlap
      FROM canon_platforms a
      JOIN canon_platforms b
        ON a.canonical_id = b.canonical_id
       AND a.platform < b.platform
      GROUP BY 1,2
    )
    SELECT * FROM pair ORDER BY overlap DESC;
    """
).df()

if pairs.empty:
    st.info("No cross-platform overlaps found.")
else:
    st.dataframe(pairs, use_container_width=True)

st.divider()

# ---------------------------------------------------------------------
# Top candidates: cross-platform + quality filters
st.subheader("Top cross-platform candidates")
min_reviews = st.slider("Min review count (per platform row)", 0, 500, 50, 25)
min_platforms = st.slider("Min platforms", 2, 3, 2, 1)

top = con.execute(
    """
    WITH joined AS (
      SELECT
        m.canonical_id,
        r.platform,
        r.restaurant_name,
        COALESCE(NULLIF(r.city,''),'Unknown') AS city,
        r.rating_value,
        r.rating_count,
        r.delivery_fee
      FROM g1_restaurant_matches m
      JOIN stg_restaurants r
        ON r.platform=m.platform AND r.restaurant_key=m.restaurant_key
      WHERE r.rating_value IS NOT NULL
        AND (r.rating_count IS NULL OR r.rating_count >= $min_reviews)
    ),
    agg AS (
      SELECT
        canonical_id,
        COUNT(DISTINCT platform) AS platform_count,
        STRING_AGG(DISTINCT platform, ', ') AS platforms,
        MAX(restaurant_name) AS representative_name,
        MAX(city) AS city,
        AVG(rating_value) AS avg_rating,
        AVG(delivery_fee) AS avg_delivery_fee,
        SUM(COALESCE(rating_count, 0)) AS total_reviews
      FROM joined
      GROUP BY 1
    )
    SELECT *
    FROM agg
    WHERE platform_count >= $min_platforms
    ORDER BY platform_count DESC, avg_rating DESC, total_reviews DESC
    LIMIT 50;
    """,
    {"min_reviews": int(min_reviews), "min_platforms": int(min_platforms)},
).df()

st.dataframe(top, use_container_width=True)

st.divider()

# ---------------------------------------------------------------------
# City hotspots: where cross-platform availability concentrates
st.subheader("City hotspots (cross-platform coverage)")
min_canon = st.slider("Min canonical restaurants per city", 10, 200, 25, 5)

city = con.execute(
    """
    WITH joined AS (
      SELECT
        m.canonical_id,
        COALESCE(NULLIF(r.city,''),'Unknown') AS city,
        r.latitude,
        r.longitude,
        r.platform
      FROM g1_restaurant_matches m
      JOIN stg_restaurants r
        ON r.platform=m.platform AND r.restaurant_key=m.restaurant_key
    ),
    canon_city AS (
      SELECT
        city,
        canonical_id,
        COUNT(DISTINCT platform) AS platform_count,
        AVG(latitude) AS lat,
        AVG(longitude) AS lon
      FROM joined
      GROUP BY 1,2
    ),
    agg AS (
      SELECT
        city,
        COUNT(*) AS canonical_restaurants,
        SUM(CASE WHEN platform_count >= 2 THEN 1 ELSE 0 END) AS cross_platform_canon,
        AVG(lat) AS lat,
        AVG(lon) AS lon
      FROM canon_city
      GROUP BY 1
    )
    SELECT *
    FROM agg
    WHERE canonical_restaurants >= $min_canon
    ORDER BY cross_platform_canon DESC, canonical_restaurants DESC
    LIMIT 50;
    """,
    {"min_canon": int(min_canon)},
).df()

st.dataframe(city, use_container_width=True)

city["lat"] = pd.to_numeric(city["lat"], errors="coerce")
city["lon"] = pd.to_numeric(city["lon"], errors="coerce")
city = city.dropna(subset=["lat", "lon"])

if not city.empty:
    st.subheader("Map (city centroids)")
    st.map(city.rename(columns={"lat": "latitude", "lon": "longitude"})[["latitude", "longitude"]])

con.close()
