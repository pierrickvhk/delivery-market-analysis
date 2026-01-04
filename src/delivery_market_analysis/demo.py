from __future__ import annotations

from pathlib import Path

import duckdb


def create_demo_db(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(db_path.as_posix())

    con.execute("CREATE SCHEMA IF NOT EXISTS demo;")

    # Minimal tables your pages rely on via views
    con.execute(
        """
        CREATE OR REPLACE TABLE demo.stg_restaurants AS
        SELECT * FROM (VALUES
          ('takeaway','r1','Pizza Uno','Antwerp',51.2194,4.4025,4.4,120,2.99),
          ('ubereats','r2','Kapsalon King','Ghent',51.0543,3.7174,4.2,80,3.49),
          ('deliveroo','r3','Hummus House',NULL,50.8503,4.3517,4.6,200,2.49)
        ) AS t(platform, restaurant_key, restaurant_name, city, latitude, longitude, rating_value, rating_count, delivery_fee);
        """
    )

    con.execute(
        """
        CREATE OR REPLACE TABLE demo.stg_menu_items AS
        SELECT * FROM (VALUES
          ('takeaway','r1','i1','Margherita','pizza classic',10.0,'pizza'),
          ('ubereats','r2','i2','Kapsalon','fries + meat',9.5,'kapsalon'),
          ('deliveroo','r3','i3','Hummus bowl','chickpeas',8.0,'hummus')
        ) AS t(platform, restaurant_key, item_key, item_name, description, price, category_name);
        """
    )

    # Minimal item search view
    con.execute(
        """
        CREATE OR REPLACE VIEW vw_menu_items_clean AS
        SELECT * FROM demo.stg_menu_items
        WHERE price IS NOT NULL AND price > 0 AND price < 500;
        """
    )

    con.execute(
        """
        CREATE OR REPLACE VIEW vw_item_search AS
        SELECT platform, restaurant_key, item_key, item_name, description, price
        FROM vw_menu_items_clean;
        """
    )

    # Minimal restaurants view compatible with pages (you might already query stg_restaurants directly)
    con.execute(
        """
        CREATE OR REPLACE VIEW stg_restaurants AS
        SELECT * FROM demo.stg_restaurants;
        """
    )

    con.execute(
        """
        CREATE OR REPLACE VIEW stg_menu_items AS
        SELECT * FROM demo.stg_menu_items;
        """
    )

    con.close()


if __name__ == "__main__":
    create_demo_db(Path("data/processed/analytics.duckdb"))
    print("[demo] created data/processed/analytics.duckdb")