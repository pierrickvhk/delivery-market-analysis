-- =========================
-- G2 Semantic Layer (v0)
-- =========================

-- -------------------------
-- Restaurants (unified)
-- -------------------------

CREATE OR REPLACE VIEW stg_restaurants AS
WITH takeaway_loc AS (
  SELECT
    ltr.restaurant_id,
    l.postalCode AS postal_code,
    l.city       AS loc_city,
    l.latitude   AS loc_latitude,
    l.longitude  AS loc_longitude
  FROM takeaway.locations_to_restaurants ltr
  JOIN takeaway.locations l
    ON l.ID = ltr.location_id
)
-- Takeaway
SELECT
  'takeaway' AS platform,
  CAST(r.primarySlug AS VARCHAR)  AS restaurant_key,
  CAST(r.name AS VARCHAR)         AS restaurant_name,
  CAST(r.address AS VARCHAR)      AS address,
  CAST(COALESCE(r.city, tl.loc_city) AS VARCHAR) AS city,
  NULLIF(CAST(tl.postal_code AS VARCHAR), '') AS postal_code,
  TRY_CAST(COALESCE(r.latitude, tl.loc_latitude) AS DOUBLE)  AS latitude,
  TRY_CAST(COALESCE(r.longitude, tl.loc_longitude) AS DOUBLE) AS longitude,
  TRY_CAST(r.ratings AS DOUBLE)        AS rating_value,
  TRY_CAST(r.ratingsNumber AS BIGINT)  AS rating_count,
  TRY_CAST(r.deliveryFee AS DOUBLE)    AS delivery_fee,
  TRY_CAST(r.minOrder AS DOUBLE)       AS min_order
FROM takeaway.restaurants r
LEFT JOIN takeaway_loc tl
  ON tl.restaurant_id = r.restaurant_id

UNION ALL
-- Deliveroo (based on your schema screenshot 3)
SELECT
  'deliveroo' AS platform,
  CAST(id AS VARCHAR) AS restaurant_key,
  CAST(name AS VARCHAR) AS restaurant_name,
  CAST(address AS VARCHAR) AS address,
  NULL AS city,
  NULLIF(CAST(postal_code AS VARCHAR), '') AS postal_code,
  TRY_CAST(latitude AS DOUBLE) AS latitude,
  TRY_CAST(longitude AS DOUBLE) AS longitude,
  TRY_CAST(rating AS DOUBLE) AS rating_value,
  TRY_CAST(rating_number AS BIGINT) AS rating_count,
  TRY_CAST(delivery_fee AS DOUBLE) AS delivery_fee,
  TRY_CAST(min_order AS DOUBLE) AS min_order
FROM deliveroo.restaurants

UNION ALL
-- UberEats (corrected: location__* columns)
SELECT
  'ubereats' AS platform,
  CAST(id AS VARCHAR) AS restaurant_key,
  CAST(title AS VARCHAR) AS restaurant_name,
  CAST(location__address AS VARCHAR) AS address,
  CAST(location__city AS VARCHAR) AS city,
  NULLIF(CAST(location__postal_code AS VARCHAR), '') AS postal_code,
  TRY_CAST(location__latitude AS DOUBLE) AS latitude,
  TRY_CAST(location__longitude AS DOUBLE) AS longitude,
  TRY_CAST(rating__rating_value AS DOUBLE) AS rating_value,
  TRY_CAST(rating__review_count AS BIGINT) AS rating_count,
  NULL AS delivery_fee,
  NULL AS min_order
FROM ubereats.restaurants
;


-- -------------------------
-- Menu items (unified)
-- -------------------------

CREATE OR REPLACE VIEW stg_menu_items AS
-- Takeaway
SELECT
  'takeaway' AS platform,
  CAST(primarySlug AS VARCHAR) AS restaurant_key,
  CAST(ID AS VARCHAR) AS item_key,
  CAST(name AS VARCHAR) AS item_name,
  CAST(description AS VARCHAR) AS description,
  TRY_CAST(price AS DOUBLE) AS price,
  NULL AS category_name
FROM takeaway.menuItems

UNION ALL
-- Deliveroo
SELECT
  'deliveroo' AS platform,
  CAST(restaurant_id AS VARCHAR) AS restaurant_key,
  CAST(id AS VARCHAR) AS item_key,
  CAST(name AS VARCHAR) AS item_name,
  CAST(description AS VARCHAR) AS description,
  TRY_CAST(price AS DOUBLE) AS price,
  NULL AS category_name
FROM deliveroo.menu_items

UNION ALL
-- UberEats
SELECT
  'ubereats' AS platform,
  CAST(restaurant_id AS VARCHAR) AS restaurant_key,
  CAST(id AS VARCHAR) AS item_key,
  CAST(name AS VARCHAR) AS item_name,
  CAST(description AS VARCHAR) AS description,
  TRY_CAST(price AS DOUBLE) AS price,
  NULL AS category_name
FROM ubereats.menu_items
;


-- -------------------------
-- Restaurant categories (unified)
-- NOTE: Takeaway uses restaurant_id, but our restaurant_key is primarySlug
-- so we map restaurant_id -> primarySlug via takeaway.restaurants.
-- -------------------------

CREATE OR REPLACE VIEW stg_restaurant_categories AS
-- UberEats: direct category strings
SELECT
  'ubereats' AS platform,
  CAST(restaurant_id AS VARCHAR) AS restaurant_key,
  CAST(category AS VARCHAR) AS category_name
FROM ubereats.restaurant_to_categories

UNION ALL
-- Deliveroo: categories table
SELECT
  'deliveroo' AS platform,
  CAST(restaurant_id AS VARCHAR) AS restaurant_key,
  CAST(name AS VARCHAR) AS category_name
FROM deliveroo.categories

UNION ALL
-- Takeaway: categories_restaurants -> categories + map to primarySlug
SELECT
  'takeaway' AS platform,
  CAST(r.primarySlug AS VARCHAR) AS restaurant_key,
  CAST(c.name AS VARCHAR) AS category_name
FROM takeaway.categories_restaurants cr
JOIN takeaway.categories c
  ON cr.category_id = c.id
JOIN takeaway.restaurants r
  ON cr.restaurant_id = r.restaurant_id
;

-- -------------------------
-- Convenience view: pizza restaurants
-- -------------------------
CREATE OR REPLACE VIEW vw_pizza_restaurants AS
SELECT
  r.platform,
  r.restaurant_key,
  r.restaurant_name,
  r.city,
  r.postal_code,
  r.latitude,
  r.longitude,
  r.rating_value,
  r.rating_count
FROM stg_restaurants r
JOIN stg_restaurant_categories c
  ON c.platform = r.platform AND c.restaurant_key = r.restaurant_key
WHERE LOWER(c.category_name) LIKE '%pizza%'
;


-- -------------------------
-- Convenience view: item search (kapsalon/hummus/veg/vegan)
-- -------------------------
CREATE OR REPLACE VIEW vw_item_search AS
SELECT
  i.platform,
  i.restaurant_key,
  i.item_key,
  i.item_name,
  i.description,
  i.price
FROM stg_menu_items i
WHERE i.price IS NOT NULL AND i.price > 0 AND i.price < 500
;
