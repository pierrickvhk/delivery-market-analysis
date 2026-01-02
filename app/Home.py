from pathlib import Path
import duckdb
import streamlit as st

st.set_page_config(page_title="Delivery Market Analysis", layout="wide")

st.title("Delivery Market Analysis (v0)")
st.caption("SQLite → DuckDB semantic layer → Streamlit dashboard")

db_path = Path("data/processed/analytics.duckdb")
if not db_path.exists():
    st.error("DuckDB ontbreekt. Run: python src/build_duckdb.py --dir data/raw")
    st.stop()

con = duckdb.connect(db_path.as_posix(), read_only=True)

restaurants = con.execute("SELECT COUNT(*) FROM stg_restaurants;").fetchone()[0]
platforms = con.execute("SELECT COUNT(DISTINCT platform) FROM stg_restaurants;").fetchone()[0]
items = con.execute("SELECT COUNT(*) FROM stg_menu_items;").fetchone()[0]

c1, c2, c3 = st.columns(3)
c1.metric("Restaurants", f"{restaurants:,}".replace(",", " "))
c2.metric("Platforms", int(platforms))
c3.metric("Menu items", f"{items:,}".replace(",", " "))

st.divider()

st.subheader("Top rated sample")
df = con.execute(
    """
    SELECT platform, restaurant_name, city, postal_code, rating_value, rating_count, delivery_fee
    FROM stg_restaurants
    ORDER BY rating_value DESC NULLS LAST, rating_count DESC NULLS LAST
    LIMIT 25;
    """
).df()
st.dataframe(df, use_container_width=True)
