"""Flatten the star schema into one tidy CSV for Tableau Public.

One row per game x region (same grain as fact_sales), with readable column names,
so Tableau needs no joins.

Usage: python tableau_export.py [db_path] [out_csv]
"""
import sqlite3
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
COLUMNS = ["Game", "Platform", "Genre", "Publisher", "Year", "Decade", "Region", "Sales (M units)"]

QUERY = """
SELECT g.name            AS "Game",
       p.platform        AS "Platform",
       ge.genre          AS "Genre",
       pu.publisher      AS "Publisher",
       y.year            AS "Year",
       y.decade          AS "Decade",
       r.region_name     AS "Region",
       f.sales_millions  AS "Sales (M units)"
FROM fact_sales f
JOIN dim_game g       USING (game_key)
JOIN dim_platform p   USING (platform_key)
JOIN dim_genre ge     USING (genre_key)
JOIN dim_publisher pu USING (publisher_key)
JOIN dim_year y       USING (year_key)
JOIN dim_region r     USING (region_key)
ORDER BY g.vgchartz_rank, r.region_key
"""


def export(db_path=ROOT / "vgsales.db", out_csv=ROOT / "tableau" / "vgsales_tableau.csv") -> int:
    out_csv = Path(out_csv)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as con:
        df = pd.read_sql_query(QUERY, con)
    df.to_csv(out_csv, index=False)
    return len(df)


if __name__ == "__main__":
    args = sys.argv[1:]
    n = export(*args) if args else export()
    print(f"wrote {n:,} rows")
