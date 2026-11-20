"""Run every named query in queries.sql against vgsales.db; write results/<name>.csv."""
import re
import sqlite3
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent


def load_queries(path=ROOT / "queries.sql") -> dict:
    text = Path(path).read_text(encoding="utf-8")
    parts = re.split(r"^-- name: (\w+)\s*$", text, flags=re.M)
    return {parts[i]: parts[i + 1].strip() for i in range(1, len(parts), 2)}


def run_all(db=ROOT / "vgsales.db", out=ROOT / "results") -> dict:
    out.mkdir(exist_ok=True)
    con = sqlite3.connect(db)
    results = {}
    for name, sql in load_queries().items():
        df = pd.read_sql_query(sql, con)
        df.to_csv(out / f"{name}.csv", index=False)
        results[name] = df
    return results


if __name__ == "__main__":
    for name, df in run_all().items():
        print(f"\n== {name} ({len(df)} rows)\n{df.head(12).to_string(index=False)}")
