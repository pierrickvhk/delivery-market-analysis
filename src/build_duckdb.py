from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path
from typing import Iterable

import duckdb
import pandas as pd

PLATFORMS = ("takeaway", "ubereats", "deliveroo")


def infer_platform(path: Path) -> str:
    stem = path.stem.lower()
    for p in PLATFORMS:
        if p in stem:
            return p
    raise ValueError(f"Cannot infer platform from filename: {path.name}. Use takeaway/ubereats/deliveroo in name.")


def list_tables(sqlite_path: Path) -> list[str]:
    con = sqlite3.connect(str(sqlite_path))
    cur = con.cursor()
    rows = cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name;"
    ).fetchall()
    con.close()
    return [r[0] for r in rows]


def iter_table_chunks(sqlite_path: Path, table: str, chunksize: int = 50_000) -> Iterable[pd.DataFrame]:
    # Critical: avoid unicode decode crashes by returning bytes for text
    con = sqlite3.connect(str(sqlite_path))
    con.text_factory = bytes  # text columns come back as bytes

    query = f'SELECT * FROM "{table}"'
    for chunk in pd.read_sql_query(query, con, chunksize=chunksize):
        yield chunk

    con.close()


def normalize_chunk_all_varchar(df: pd.DataFrame) -> pd.DataFrame:
    # Replace NaN with None
    df = df.where(pd.notnull(df), None)

    def norm(x):
        if x is None:
            return None
        if isinstance(x, (bytes, bytearray)):
            return x.decode("utf-8", errors="replace")
        # keep as string for consistent VARCHAR raw layer
        return str(x)

    for col in df.columns:
        df[col] = df[col].map(norm)

    return df


def create_table_all_varchar(con: duckdb.DuckDBPyConnection, full_name: str, columns: list[str]) -> None:
    cols_sql = ", ".join([f'"{c}" VARCHAR' for c in columns])
    con.execute(f"DROP TABLE IF EXISTS {full_name};")
    con.execute(f"CREATE TABLE {full_name} ({cols_sql});")


def insert_chunk(con: duckdb.DuckDBPyConnection, full_name: str, df: pd.DataFrame) -> None:
    con.register("tmp_df", df)
    con.execute(f"INSERT INTO {full_name} SELECT * FROM tmp_df;")
    con.unregister("tmp_df")


def ingest_sqlite_via_python(con: duckdb.DuckDBPyConnection, sqlite_path: Path, platform: str) -> None:
    con.execute(f"CREATE SCHEMA IF NOT EXISTS {platform};")

    tables = list_tables(sqlite_path)
    print(f"[ingest] {platform}: {len(tables)} tables from {sqlite_path.name} (python fallback)")

    for t in tables:
        full_name = f"{platform}.\"{t}\""
        first = True
        for raw_chunk in iter_table_chunks(sqlite_path, t):
            chunk = normalize_chunk_all_varchar(raw_chunk)

            if first:
                create_table_all_varchar(con, full_name, list(chunk.columns))
                first = False

            insert_chunk(con, full_name, chunk)

        print(f"[ingest] {platform}: loaded {t}")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--dir", default="data/raw", help="Directory containing *.db files")
    p.add_argument("--out", default="data/processed/analytics.duckdb", help="DuckDB output file")
    args = p.parse_args()

    raw_dir = Path(args.dir)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    db_files = sorted(raw_dir.glob("*.db"))
    if not db_files:
        raise FileNotFoundError(f"No .db files found in {raw_dir.resolve()}")

    con = duckdb.connect(out_path.as_posix())
    con.execute("PRAGMA threads=4;")

    for db in db_files:
        platform = infer_platform(db)
        ingest_sqlite_via_python(con, db, platform)

    total = con.execute(
        "SELECT COUNT(*) FROM information_schema.tables "
        "WHERE table_schema IN ('takeaway','ubereats','deliveroo');"
    ).fetchone()[0]
    print(f"[done] Total ingested tables: {total}")

    con.close()


if __name__ == "__main__":
    main()
