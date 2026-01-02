from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

import duckdb


PLATFORMS = {"takeaway", "ubereats", "deliveroo"}


def infer_platform(path: Path) -> str:
    name = path.stem.lower()
    for p in PLATFORMS:
        if p in name:
            return p
    raise ValueError(f"Cannot infer platform from filename: {path.name}. Expected one of {PLATFORMS}.")


def list_sqlite_tables(sqlite_path: Path) -> list[str]:
    con = sqlite3.connect(str(sqlite_path))
    cur = con.cursor()
    rows = cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name;"
    ).fetchall()
    con.close()
    return [r[0] for r in rows]


def ingest_one_db(duck: duckdb.DuckDBPyConnection, sqlite_path: Path, platform: str) -> None:
    tables = list_sqlite_tables(sqlite_path)
    print(f"[ingest] {platform}: {len(tables)} tables from {sqlite_path.name}")

    duck.execute(f"CREATE SCHEMA IF NOT EXISTS {platform};")

    # Fast path
    try:
        duck.execute("INSTALL sqlite_scanner;")
        duck.execute("LOAD sqlite_scanner;")
        for t in tables:
            duck.execute(f"DROP TABLE IF EXISTS {platform}.{t};")
            duck.execute(
                f"""
                CREATE TABLE {platform}.{t} AS
                SELECT * FROM sqlite_scan('{sqlite_path.as_posix()}', '{t}');
                """
            )
        print(f"[ingest] {platform}: sqlite_scanner")
        return
    except Exception as e1:
        print(f"[ingest] {platform}: sqlite_scanner failed: {e1}")

    # Fallback
    duck.execute("INSTALL sqlite;")
    duck.execute("LOAD sqlite;")
    duck.execute("DETACH DATABASE IF EXISTS s;")
    duck.execute(f"ATTACH '{sqlite_path.as_posix()}' AS s (TYPE sqlite);")
    for t in tables:
        duck.execute(f"DROP TABLE IF EXISTS {platform}.{t};")
        duck.execute(f"CREATE TABLE {platform}.{t} AS SELECT * FROM s.{t};")
    duck.execute("DETACH DATABASE s;")
    print(f"[ingest] {platform}: ATTACH fallback")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--dir", default="data/raw", help="Folder containing *.db SQLite files")
    p.add_argument("--out", default="data/processed/analytics.duckdb", help="DuckDB output path")
    args = p.parse_args()

    raw_dir = Path(args.dir)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    db_files = sorted(raw_dir.glob("*.db"))
    if not db_files:
        raise FileNotFoundError(f"No .db files found in {raw_dir.resolve()}")

    duck = duckdb.connect(str(out_path))
    duck.execute("PRAGMA threads=4;")

    for f in db_files:
        platform = infer_platform(f)
        ingest_one_db(duck, f, platform)

    tables = duck.execute(
        "SELECT table_schema, table_name FROM information_schema.tables "
        "WHERE table_schema IN ('takeaway','ubereats','deliveroo') ORDER BY 1,2;"
    ).fetchall()
    print(f"[done] Total ingested tables: {len(tables)}")
    duck.close()


if __name__ == "__main__":
    main()
