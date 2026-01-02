# 📦 Delivery Market Analysis

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![DuckDB](https://img.shields.io/badge/DuckDB-enabled-yellow.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-dashboard-red.svg)
![Plotly](https://img.shields.io/badge/Plotly-charts-orange.svg)
![RapidFuzz](https://img.shields.io/badge/RapidFuzz-matching-lightgrey.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)

## 🧠 Short Intro

BeCode project (Data Science & AI Bootcamp).  
In 4 days I built an end-to-end delivery market analysis across three platforms, from raw SQLite databases to a DuckDB semantic layer and a Streamlit dashboard.

---

## 🚀 Highlights

- **End-to-end pipeline:** SQLite → DuckDB (semantic layer) → Streamlit dashboard  
- **SQL-heavy analysis** with clean, reusable views (`stg_*` and convenience views)  
- **Cross-platform entity resolution (G1)** to quantify overlap between platforms  
- **Geospatial insights:** coverage hotspots, dead zones proxy, dish availability maps  
- **Data quality handling:** invalid prices filtered, UberEats hours parsed from minutes since midnight  

---

## 📘 BeCode Assignment

### 🎯 Context

We analyze food delivery data to uncover actionable insights for restaurant partners and consumers.  
The goal is to explore trends, customer preferences, and market dynamics.

### ✅ Must-have business questions

- Price distribution of menu items  
- Distribution of restaurants per location  
- Top 10 pizza restaurants by rating  
- Map locations offering kapsalons (or another dish) and their average price  

### 💡 Open-ended questions covered

- Best price-to-rating ratio (value proxy)  
- Delivery dead zones (low coverage proxy using geo and location aggregation)  
- Vegetarian and vegan availability by area (menu text heuristic)  
- **WHO (World Hummus Order):** top 3 hummus restaurants  
- Original questions (examples):  
  - Price outliers per platform (z-score)  
  - Chains vs independent proxy (repeated names across cities)  
  - Late-night availability on UberEats using hours data  

---

## 🧑‍💻 What I Learned / Personal Note

This was a 4-day BeCode project and I genuinely enjoyed it because it combines SQL and Python in one realistic workflow. I learned a lot about designing a semantic layer, dealing with messy source data, and turning an analysis into a small analytics product.

Instead of stopping at a notebook, I pushed it further by building an interactive Streamlit app to make the insights explorable and presentation-ready.

---

## 💾 Data

- **Input format:** SQLite databases (not committed to Git)  
  - `deliveroo.db`  
  - `takeaway.db`  
  - `ubereats.db`  

---

## 🛠 Tech Stack

- Python, Pandas  
- **DuckDB** (analytics engine + semantic layer)  
- **Streamlit** (dashboard)  
- **Plotly** (charts)  
- **RapidFuzz** (fuzzy matching for G1)  

---

## 📁 Repository Structure

```text
DELIVERY-MARKET-ANALYSIS/
├── .venv/
├── .vscode/
├── app/
│   ├── Home.py
│   └── pages/
│       ├── 2_Pricing.py
│       ├── 3_Locations.py
│       ├── 4_Value.py
│       ├── 5_Geo.py
│       ├── 6_VegVegan.py
│       ├── 7_CrossPlatform.py
│       ├── 8_Outliers.py
│       ├── 9_Chains.py
│       └── 10_LateNight.py
├── assets/
│   └── screenshots/
├── data/
├── sql/
│   └── 90_views_semantic.sql
├── src/
│   ├── __init__.py
│   ├── apply_sql.py
│   ├── build_duckdb.py
│   └── delivery_market_analysis/
│       ├── __init__.py
│       ├── matching.py
│       └── queries.py
├── tests/
│   ├── test_ingest_views.py
│   └── test_smoke.py
├── Makefile
├── pyproject.toml
└── README.md
```

---

## ▶️ How to Run Locally

### Prerequisites

- Python 3.11+  
- Virtual environment  

### Installation

```bash
pip install -e ".[dev]"
```

### Build analytics database (SQLite → DuckDB)

```bash
python src/build_duckdb.py --dir data/raw
python src/apply_sql.py
```

### Build G1 matching (cross-platform entity resolution)

```bash
python -m delivery_market_analysis.matching
```

### Run dashboard

```bash
streamlit run app/Home.py
```

---

## 📊 Dashboard Pages (For Reviewers)

- **Home:** dataset overview and sanity checks  
- **Pricing:** menu item price distribution (clean prices)  
- **Locations:** restaurant distribution per city + map  
- **Geo dish map:** kapsalon (or keyword) locations + average price  
- **Value:** best price-to-rating proxy + top pizza restaurants  
- **Veg/Vegan:** availability by area (text heuristic)  
- **WHO (Hummus):** top hummus restaurants  
- **Cross-platform (G1):** overlap distribution + pairwise overlap + top candidates + hotspots  
- **Outliers:** extreme menu item prices per platform (z-score)  
- **Chains:** chain vs independent proxy  
- **Late night:** UberEats open-late analysis based on hours encoding  

---

## 📌 Method Notes (For Coaches / Judges)

### Semantic Layer

- Raw tables remain platform-scoped in DuckDB schemas  
- `stg_*` views standardize types and fields across platforms  
- Convenience views keep queries readable and reusable across the dashboard  

### Data Quality Rules

- **Prices:** invalid values are filtered (`NULL` / `<= 0`), extreme values handled for visualization  
- **Location:** not all sources provide identical location fields (e.g., Deliveroo restaurants have no city)  
- **Hours:** UberEats `end_time` is stored as minutes since midnight and converted to `TIME`  

### G1 Entity Resolution (Cross-platform Matching)

**Approach:**

- Normalize restaurant names (lowercase, punctuation removal, stopwords)  
- Block candidates by normalized city to reduce false positives  
- Fuzzy match (token-set ratio)  
- Union-Find clustering to produce canonical restaurant IDs  

**Outputs:**

- `g1_restaurant_matches`  
- `vw_canonical_restaurants`  

---

## ⚠️ Limitations

- Text-based dish/veg detection is heuristic and may undercount some items  
- Entity resolution is probabilistic; blocking and thresholds reduce false positives  
- Cross-platform comparisons depend on available fields (fees/hours are not uniform across sources)  

---

## ✅ Evaluation Checklist

### Coverage

- Must-have questions: implemented in dashboard pages (Pricing, Locations, Value, Geo dish map)  
- Open-ended questions: value proxy, dead zones proxy, veg/vegan, WHO hummus, and original questions via Outliers / Chains / Late Night  
- Nice-to-have: semantic layer for readable/optimized SQL, cross-platform overlap via G1  

---

## 🌟 STAR (Presentation Summary)

### Situation

Three delivery datasets with different schemas and uneven data quality.

### Task

Produce actionable insights and present them clearly, including cross-platform comparisons.

### Action

Built a DuckDB semantic layer, implemented cross-platform restaurant matching (G1), and shipped a Streamlit dashboard including geospatial and pricing insights.

### Result

A reproducible analytics workflow and a story-driven dashboard answering the required business questions and advanced insights.

---

## 👤 Author

Pierrick Van Hoecke — BeCode Data Science & AI Bootcamp

