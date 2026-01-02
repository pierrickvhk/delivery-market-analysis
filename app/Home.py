from pathlib import Path
import duckdb
import streamlit as st

st.set_page_config(page_title="Delivery Market Analysis", layout="wide")
st.title("Delivery Market Analysis (v0)")

db_path = Path("data/processed/analytics.duckdb")
if not db_path.exists():
    st.error("Run eerst: python src/build_duckdb.py --dir data/raw")
    st.stop()

con = duckdb.connect(db_path.as_posix(), read_only=True)

# KPI's uit unified views
k1 = con.execute("SELECT COUNT(*) FROM stg_restaurants;").fetchone()[0]
k2 = con.execute("SELECT COUNT(DISTINCT platform) FROM stg_restaurants;").fetchone()[0]
k3 = con.execute("SELECT COUNT(*) FROM stg_menu_items;").fetchone()[0]

c1, c2, c3 = st.columns(3)
c1.metric("Restaurants", f"{k1:,}".replace(",", " "))
c2.metric("Platforms", k2)
c3.metric("Menu items", f"{k3:,}".replace(",", " "))

st.divider()

st.subheader("Sample: restaurants")
df = con.execute(
    """
    SELECT platform, restaurant_name, city, postal_code, rating_value, delivery_fee
    FROM stg_restaurants
    ORDER BY rating_value DESC NULLS LAST
    LIMIT 20;
    """
).df()
st.dataframe(df, use_container_width=True)
