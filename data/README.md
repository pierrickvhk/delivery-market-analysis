## Data

This project uses SQLite datasets provided by **BeCode (Data Science & AI Bootcamp)** as its primary data source.

The raw datasets are **not included in this repository** for licensing and distribution reasons.

---

### 📁 Expected raw data files

Place the three SQLite databases in the following directory:

```text
data/raw/
├── deliveroo.db
├── takeaway.db
└── ubereats.db
```

These files are intentionally **excluded from version control**.

---

### 🗄️ Generated analytics database

During execution, the pipeline builds a DuckDB analytics database at:

```text
data/processed/analytics.duckdb
```

This file is also **not committed to Git**, as it is fully reproducible from the raw SQLite inputs.

---

## ▶️ Running the pipeline with BeCode datasets

If you have access to the BeCode SQLite files, you can run the full analytics pipeline.

### 1) Install dependencies

```bash
pip install -e ".[dev]"
```

### 2) Build the analytics database (SQLite → DuckDB)

```bash
python src/build_duckdb.py --dir data/raw
python src/apply_sql.py
```

### 3) Run cross-platform entity matching (G1)

```bash
dma match
```

**Alternative:**

```bash
python -m delivery_market_analysis.matching
```

### 4) Launch the dashboard

```bash
streamlit run app/Home.py
```

---

## 🧪 Demo mode (no BeCode data required)

For reviewers or users without access to the BeCode datasets, the project includes a demo mode that enables a full end-to-end smoke test.

### 1) Generate a demo analytics database

```bash
dma demo
```

**or:**

```bash
make demo
```

### 2) Start the dashboard

```bash
make run
```

**or:**

```bash
streamlit run app/Home.py
```

The demo dataset is intentionally minimal and exists solely to validate:

- the data pipeline  
- the semantic layer  
- the Streamlit UI  

---

## 📝 Notes for reviewers

- The demo data is not representative of real delivery market metrics.  
- Full analytical insights and conclusions require the original BeCode datasets.  
- The goal of demo mode is **reproducibility and pipeline validation**, not analysis depth.