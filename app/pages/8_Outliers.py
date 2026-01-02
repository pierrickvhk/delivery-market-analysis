from __future__ import annotations

from pathlib import Path
import duckdb
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Outliers", layout="wide")
st.title("Outliers")
st.caption("Extreme menu item prices using z-scores per platform (data quality + insights).")

con = duckdb.connect(Path("data/processed/analytics.duckdb").as_posix(), read_only=True)

platforms = ["All"] + [r[0] for r in con.execute("SELECT DISTINCT platform FROM vw_item_search ORDER BY 1;").fetchall()]
sel_platform = st.selectbox("Platform", platforms, index=0)
z_thr = st.slider("Z-score threshold", 2.0, 6.0, 3.0, 0.5)

params = {"platform": None if sel_platform == "All" else sel_platform, "z": float(z_thr)}

df = con.execute(
    """
    WITH stats AS (
      SELECT platform,
             AVG(price) AS mu,
             STDDEV_SAMP(price) AS sigma
      FROM vw_item_search
      GROUP BY 1
    )
    SELECT
      i.platform,
      r.restaurant_name,
      r.city,
      i.item_name,
      i.price,
      (i.price - s.mu) / NULLIF(s.sigma, 0) AS z_score
    FROM vw_item_search i
    JOIN stats s USING (platform)
    JOIN stg_restaurants r
      ON r.platform = i.platform AND r.restaurant_key = i.restaurant_key
    WHERE s.sigma IS NOT NULL
      AND ABS((i.price - s.mu) / NULLIF(s.sigma, 0)) >= $z
      AND ($platform IS NULL OR i.platform = $platform)
    ORDER BY ABS(z_score) DESC
    LIMIT 100;
    """,
    params,
).df()

st.dataframe(df, use_container_width=True)

if not df.empty:
    fig = px.scatter(df, x="price", y="z_score", hover_name="item_name", color="platform" if sel_platform == "All" else None)
    st.plotly_chart(fig, use_container_width=True)
