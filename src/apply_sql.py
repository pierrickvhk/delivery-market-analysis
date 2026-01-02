from pathlib import Path
import duckdb

DB_PATH = Path("data/processed/analytics.duckdb")
SQL_PATH = Path("sql/90_views_semantic.sql")


def main() -> None:
    if not DB_PATH.exists():
        raise FileNotFoundError(DB_PATH)
    if not SQL_PATH.exists():
        raise FileNotFoundError(SQL_PATH)

    con = duckdb.connect(DB_PATH.as_posix())
    con.execute(SQL_PATH.read_text(encoding="utf-8"))
    # sanity
    views = con.execute(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_schema='main' AND table_type='VIEW' ORDER BY 1;"
    ).fetchall()
    print("Views:", [v[0] for v in views])
    con.close()


if __name__ == "__main__":
    main()
