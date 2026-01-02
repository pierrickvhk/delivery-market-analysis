-- G2: Unified staging (cross-platform)

CREATE OR REPLACE VIEW stg_restaurants AS
SELECT
  'takeaway' AS platform,
  CAST(primarySlug AS VARCHAR) AS restaurant_key,
  CAST(name AS VARCHAR) AS restaurant_name,
  CAST(address AS VARCHAR) AS address,
  CAST(city AS VARCHAR) AS city,
  NULLIF(CAST(postalCode AS VARCHAR), '') AS postal_code,
  TRY_CAST(latitude AS DOUBLE) AS latitude,
  TRY_CAST(longitude AS DOUBLE) AS longitude,
  TRY_CAST(ratings AS DOUBLE) AS rating_value,
  TRY_CAST(ratingsNumber AS BIGINT) AS rating_count,
  TRY_CAST(deliveryFee AS DOUBLE) AS delivery_fee,
  TRY_CAST(minOrder AS DOUBLE) AS min_order
FROM takeaway.restaurants

UNION ALL
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
SELECT
  'ubereats' AS platform,
  CAST(id AS VARCHAR) AS restaurant_key,
  CAST(title AS VARCHAR) AS restaurant_name,
  CAST(location_address AS VARCHAR) AS address,
  CAST(location_city AS VARCHAR) AS city,
  NULLIF(CAST(location_postal_code AS VARCHAR), '') AS postal_code,
  TRY_CAST(location_latitude AS DOUBLE) AS latitude,
  TRY_CAST(location_longitude AS DOUBLE) AS longitude,
  TRY_CAST(rating__rating_value AS DOUBLE) AS rating_value,
  TRY_CAST(rating__review_count AS BIGINT) AS rating_count,
  NULL AS delivery_fee,
  NULL AS min_order
FROM ubereats.restaurants
;

-- Items (price distribution, kapsalon/hummus/veg/vegan)
CREATE OR REPLACE VIEW stg_menu_items AS
SELECT
  'takeaway' AS platform,
  CAST(primarySlug AS VARCHAR) AS restaurant_key,
  CAST(ID AS VARCHAR) AS item_key,
  CAST(name AS VARCHAR) AS item_name,
  CAST(description AS VARCHAR) AS description,
  TRY_CAST(price AS DOUBLE) AS price,
  NULL AS category_name,
  TRY_CAST(alcoholContent AS DOUBLE) AS alcohol_content
FROM takeaway.menuItems

UNION ALL
SELECT
  'deliveroo' AS platform,
  CAST(restaurant_id AS VARCHAR) AS restaurant_key,
  CAST(id AS VARCHAR) AS item_key,
  CAST(name AS VARCHAR) AS item_name,
  CAST(description AS VARCHAR) AS description,
  TRY_CAST(price AS DOUBLE) AS price,
  NULL AS category_name,
  TRY_CAST(alcohol AS DOUBLE) AS alcohol_content
FROM deliveroo.menu_items

UNION ALL
SELECT
  'ubereats' AS platform,
  CAST(restaurant_id AS VARCHAR) AS restaurant_key,
  CAST(id AS VARCHAR) AS item_key,
  CAST(name AS VARCHAR) AS item_name,
  CAST(description AS VARCHAR) AS description,
  TRY_CAST(price AS DOUBLE) AS price,
  NULL AS category_name,
  NULL AS alcohol_content
FROM ubereats.menu_items
;

-- Restaurant categories (for pizza / cuisine overlap)
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
-- Takeaway: categories_restaurants -> categories
SELECT
  'takeaway' AS platform,
  CAST(cr.restaurant_id AS VARCHAR) AS restaurant_key,
  CAST(c.name AS VARCHAR) AS category_name
FROM takeaway.categories_restaurants cr
JOIN takeaway.categories c
  ON cr.category_id = c.id
;
