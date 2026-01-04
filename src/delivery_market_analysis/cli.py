from __future__ import annotations

import argparse
from pathlib import Path

from delivery_market_analysis.demo import create_demo_db


def main() -> None:
    p = argparse.ArgumentParser(prog="dma")
    sub = p.add_subparsers(dest="cmd", required=True)

    demo = sub.add_parser("demo", help="Create a tiny demo analytics.duckdb")
    demo.add_argument("--out", default="data/processed/analytics.duckdb")

    args = p.parse_args()

    if args.cmd == "demo":
        create_demo_db(Path(args.out))


if __name__ == "__main__":
    main()
