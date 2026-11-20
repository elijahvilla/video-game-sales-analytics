"""ETL: vgsales.csv -> SQLite star schema (vgsales.db).

Star schema
  fact_sales(game_key, platform_key, genre_key, publisher_key, year_key, region_key, sales_millions)
  dim_game, dim_platform, dim_genre, dim_publisher, dim_year, dim_region

Usage: python etl.py [raw_csv] [db_path]
"""
import sqlite3
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
REGIONS = {"NA": "NA_Sales", "EU": "EU_Sales", "JP": "JP_Sales", "Other": "Other_Sales"}
REGION_NAMES = {"NA": "North America", "EU": "Europe", "JP": "Japan", "Other": "Rest of World"}


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """Drop rows with unknown year/publisher, normalize types, trim text."""
    df = df.copy()
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
    df["Publisher"] = df["Publisher"].replace({"Unknown": None, "N/A": None})
    df = df.dropna(subset=["Year", "Publisher", "Name", "Platform", "Genre"])
    df["Year"] = df["Year"].astype(int)
    df = df[df["Year"] <= 2016]  # 2017+ rows are a handful of incomplete pre-release records
    for c in ["Name", "Platform", "Genre", "Publisher"]:
        df[c] = df[c].astype(str).str.strip()
    return df.reset_index(drop=True)


def _dim(values, key, col):
    d = pd.DataFrame({col: sorted(set(values))})
    d.insert(0, key, range(1, len(d) + 1))
    return d


def run_etl(raw_csv=ROOT / "data" / "raw" / "vgsales.csv", db_path=ROOT / "vgsales.db") -> dict:
    raw = pd.read_csv(raw_csv)
    df = clean(raw)
    df["game_key"] = range(1, len(df) + 1)
    dim_game = df[["game_key", "Rank", "Name"]].rename(columns={"Rank": "vgchartz_rank", "Name": "name"})
    dim_platform = _dim(df["Platform"], "platform_key", "platform")
    dim_genre = _dim(df["Genre"], "genre_key", "genre")
    dim_publisher = _dim(df["Publisher"], "publisher_key", "publisher")
    dim_year = _dim(df["Year"], "year_key", "year")
    dim_year["decade"] = (dim_year["year"] // 10 * 10).astype(str) + "s"
    dim_region = pd.DataFrame({"region_key": range(1, len(REGIONS) + 1), "region": list(REGIONS),
                               "region_name": [REGION_NAMES[r] for r in REGIONS]})
    keyed = (df.merge(dim_platform, left_on="Platform", right_on="platform")
               .merge(dim_genre, left_on="Genre", right_on="genre")
               .merge(dim_publisher, left_on="Publisher", right_on="publisher")
               .merge(dim_year, left_on="Year", right_on="year"))
    long = keyed.melt(id_vars=["game_key", "platform_key", "genre_key", "publisher_key", "year_key"],
                      value_vars=list(REGIONS.values()), var_name="col", value_name="sales_millions")
    long["region"] = long["col"].map({v: k for k, v in REGIONS.items()})
    fact = long.merge(dim_region[["region_key", "region"]], on="region")[
        ["game_key", "platform_key", "genre_key", "publisher_key", "year_key", "region_key", "sales_millions"]]

    db_path = Path(db_path)
    if db_path.exists():
        db_path.unlink()
    con = sqlite3.connect(db_path)
    for name, frame in [("dim_game", dim_game), ("dim_platform", dim_platform), ("dim_genre", dim_genre),
                        ("dim_publisher", dim_publisher), ("dim_year", dim_year), ("dim_region", dim_region),
                        ("fact_sales", fact)]:
        frame.to_sql(name, con, index=False)
    con.executescript("""
        CREATE INDEX ix_fact_game ON fact_sales(game_key);
        CREATE INDEX ix_fact_region ON fact_sales(region_key);
        CREATE INDEX ix_fact_year ON fact_sales(year_key);
    """)
    con.commit()
    con.close()
    return {"raw_rows": len(raw), "clean_rows": len(df), "dropped_rows": len(raw) - len(df),
            "fact_rows": len(fact), "platforms": len(dim_platform), "genres": len(dim_genre),
            "publishers": len(dim_publisher), "years": f"{df['Year'].min()}-{df['Year'].max()}"}


if __name__ == "__main__":
    args = sys.argv[1:]
    print(run_etl(*args) if args else run_etl())
