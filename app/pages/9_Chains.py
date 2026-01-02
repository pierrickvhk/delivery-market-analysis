from __future__ import annotations

from pathlib import Path
import duckdb
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Chains", layout="wide")
st.title("Chains")
st.caption("Chain vs independent proxy using repeated restaurant names across cities.")

con = duckdb.connect(Path("data/processed/analytics.duckdb").as_posix(), read_only=True)

min_locations = st.slider("Minimum distinct cities to qualify as chain", 2, 10, 3, 1)

chains = con.execute(
    """
    WITH base AS (
      SELECT
        platform,
        LOWER(TRIM(restaurant_name)) AS name_norm,
        COALESCE(NULLIF(city,''),'Unknown') AS city,
        rating_value,
        delivery_fee
      FROM stg_restaurants
      WHERE restaurant_name IS NOT NULL
    ),
    agg AS (
      SELECT
        name_norm,
        COUNT(*) AS rows_total,
        COUNT(DISTINCT city) AS cities,
        COUNT(DISTINCT platform) AS platforms,
        AVG(rating_value) AS avg_rating,
        AVG(delivery_fee) AS avg_delivery_fee
      FROM base
      GROUP BY 1
    )
    SELECT *
    FROM agg
    WHERE cities >= $min_locations
    ORDER BY cities DESC, rows_total DESC
    LIMIT 50;
    """,
    {"min_locations": int(min_locations)},
).df()

st.subheader("Top chains (proxy)")
st.dataframe(chains, use_container_width=True)

st.divider()

comp = con.execute(
    """
    WITH base AS (
      SELECT
        LOWER(TRIM(restaurant_name)) AS name_norm,
        COALESCE(NULLIF(city,''),'Unknown') AS city,
        rating_value,
        delivery_fee
      FROM stg_restaurants
      WHERE restaurant_name IS NOT NULL
    ),
    name_city AS (
      SELECT name_norm, COUNT(DISTINCT city) AS cities
      FROM base
      GROUP BY 1
    ),
    tagged AS (
      SELECT
        b.*,
        CASE WHEN nc.cities >= $min_locations THEN 'chain' ELSE 'independent' END AS group_tag
      FROM base b
      JOIN name_city nc USING (name_norm)
    )
    SELECT
      group_tag,
      COUNT(*) AS rows,
      AVG(rating_value) AS avg_rating,
      AVG(delivery_fee) AS avg_delivery_fee
    FROM tagged
    GROUP BY 1
    ORDER BY 1;
    """,
    {"min_locations": int(min_locations)},
).df()

st.subheader("Chain vs independent summary")
st.dataframe(comp, use_container_width=True)

if not chains.empty:
    fig = px.bar(chains.head(20), x="cities", y="name_norm", orientation="h")
    st.plotly_chart(fig, use_container_width=True)
