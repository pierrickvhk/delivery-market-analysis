from pathlib import Path
import duckdb


def test_duckdb_exists() -> None:
    assert Path("data/processed/analytics.duckdb").exists()


def test_views_exist() -> None:
    con = duckdb.connect("data/processed/analytics.duckdb", read_only=True)
    views = {r[0] for r in con.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_schema='main' AND table_type='VIEW';"
    ).fetchall()}
    con.close()
    assert {"stg_restaurants", "stg_menu_items", "stg_restaurant_categories"} <= views
