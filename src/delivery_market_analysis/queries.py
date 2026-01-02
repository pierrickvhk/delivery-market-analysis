from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

import duckdb
import pandas as pd


@dataclass(frozen=True)
class Filters:
    platform: Optional[str] = None
    city: Optional[str] = None
    category: Optional[str] = None


def _where(filters: Filters) -> tuple[str, Dict[str, Any]]:
    clauses = []
    params: Dict[str, Any] = {}
    if filters.platform:
        clauses.append("platform = $platform")
        params["platform"] = filters.platform
    if filters.city:
        clauses.append("city = $city")
        params["city"] = filters.city
    if filters.category:
        clauses.append("LOWER(category_name) = LOWER($category)")
        params["category"] = filters.category
    if not clauses:
        return "", params
    return "WHERE " + " AND ".join(clauses), params


def query_df(con: duckdb.DuckDBPyConnection, sql: str, params: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
    if params:
        return con.execute(sql, params).df()
    return con.execute(sql).df()
