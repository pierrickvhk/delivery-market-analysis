from __future__ import annotations

import re
from dataclasses import dataclass
from math import asin, cos, radians, sin, sqrt
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import duckdb
import pandas as pd
from rapidfuzz import fuzz, process


STOPWORDS = {
    "restaurant", "resto", "snack", "bar", "grill", "kitchen", "takeaway", "delivery",
    "the", "de", "het", "van", "and", "&"
}

PLATFORM_ORDER = {"takeaway": 0, "deliveroo": 1, "ubereats": 2}


def normalize_text(s: Optional[str]) -> str:
    if not s:
        return ""
    s = s.lower()
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    tokens = [t for t in s.split() if t not in STOPWORDS]
    return " ".join(tokens)


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return 2 * r * asin(sqrt(a))


@dataclass
class Node:
    platform: str
    restaurant_key: str
    name_norm: str
    city_norm: str
    lat: Optional[float]
    lon: Optional[float]


class UnionFind:
    def __init__(self) -> None:
        self.parent: Dict[str, str] = {}

    def find(self, x: str) -> str:
        self.parent.setdefault(x, x)
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def union(self, a: str, b: str) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return
        # stable root: lexicographically smallest
        self.parent[max(ra, rb)] = min(ra, rb)


def node_id(p: str, k: str) -> str:
    return f"{p}:{k}"


def best_edges_for_city(nodes: List[Node], limit: int = 5) -> List[Tuple[str, str, int]]:
    """
    Create edges between platforms using fuzzy matching, blocked by city.
    For each node, search best matches in other platforms (top N).
    Returns edges: (id_a, id_b, score)
    """
    by_platform: Dict[str, List[Node]] = {}
    for n in nodes:
        by_platform.setdefault(n.platform, []).append(n)

    edges: List[Tuple[str, str, int]] = []
    platforms = list(by_platform.keys())

    for p in platforms:
        for n in by_platform[p]:
            for q in platforms:
                if q == p:
                    continue
                candidates = by_platform[q]
                cand_names = [c.name_norm for c in candidates]
                if not cand_names or not n.name_norm:
                    continue

                matches = process.extract(
                    n.name_norm,
                    cand_names,
                    scorer=fuzz.token_set_ratio,
                    limit=limit,
                )

                for cand_name, score, idx in matches:
                    c = candidates[idx]

                    # optional geo constraint if both have coords
                    geo_ok = True
                    if n.lat is not None and n.lon is not None and c.lat is not None and c.lon is not None:
                        d = haversine_km(n.lat, n.lon, c.lat, c.lon)
                        geo_ok = d <= 1.0  # 1 km

                    # thresholds
                    if score >= 90 and geo_ok:
                        edges.append((node_id(n.platform, n.restaurant_key), node_id(c.platform, c.restaurant_key), int(score)))
                    elif score >= 85 and geo_ok and (n.lat is not None and c.lat is not None):
                        edges.append((node_id(n.platform, n.restaurant_key), node_id(c.platform, c.restaurant_key), int(score)))

    return edges


def build_matches(db_path: Path) -> None:
    con = duckdb.connect(db_path.as_posix())

    df = con.execute(
        """
        SELECT platform, restaurant_key, restaurant_name, city, latitude, longitude
        FROM stg_restaurants
        """
    ).df()

    df["name_norm"] = df["restaurant_name"].map(normalize_text)
    df["city_norm"] = df["city"].map(normalize_text)

    nodes: List[Node] = []
    for r in df.itertuples(index=False):
        lat = float(r.latitude) if r.latitude is not None and str(r.latitude) != "" else None
        lon = float(r.longitude) if r.longitude is not None and str(r.longitude) != "" else None
        nodes.append(
            Node(
                platform=str(r.platform),
                restaurant_key=str(r.restaurant_key),
                name_norm=str(r.name_norm),
                city_norm=str(r.city_norm),
                lat=lat,
                lon=lon,
            )
        )

    uf = UnionFind()

    # block by city_norm to keep it fast
    city_groups: Dict[str, List[Node]] = {}
    for n in nodes:
        key = n.city_norm or "unknown"
        city_groups.setdefault(key, []).append(n)

    for city_key, group in city_groups.items():
        edges = best_edges_for_city(group, limit=5)
        for a, b, _score in edges:
            uf.union(a, b)

    # canonical id = root
    records = []
    for n in nodes:
        nid = node_id(n.platform, n.restaurant_key)
        canonical = uf.find(nid)
        records.append((canonical, n.platform, n.restaurant_key))

    match_df = pd.DataFrame(records, columns=["canonical_id", "platform", "restaurant_key"])

    con.execute("DROP TABLE IF EXISTS g1_restaurant_matches;")
    con.execute("CREATE TABLE g1_restaurant_matches AS SELECT * FROM match_df;")

    # helper view for summary
    con.execute(
        """
        CREATE OR REPLACE VIEW vw_canonical_restaurants AS
        SELECT
          m.canonical_id,
          COUNT(*) AS platform_rows,
          COUNT(DISTINCT m.platform) AS platform_count,
          STRING_AGG(DISTINCT m.platform, ', ') AS platforms
        FROM g1_restaurant_matches m
        GROUP BY 1;
        """
    )

    con.close()


def main() -> None:
    db_path = Path("data/processed/analytics.duckdb")
    if not db_path.exists():
        raise FileNotFoundError(db_path)
    build_matches(db_path)
    print("G1 matching built: g1_restaurant_matches + vw_canonical_restaurants")


if __name__ == "__main__":
    main()
