import sqlite3
from pathlib import Path

import pandas as pd
import pytest

from etl import run_etl
from tableau_export import COLUMNS, export

RAW = Path(__file__).resolve().parent.parent / "data" / "raw" / "vgsales.csv"


@pytest.fixture(scope="module")
def exported(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("tab")
    db = tmp / "vgsales.db"
    run_etl(RAW, db)
    out = tmp / "vgsales_tableau.csv"
    export(db, out)
    return db, pd.read_csv(out)


def test_one_row_per_fact_row(exported):
    db, df = exported
    n_fact = sqlite3.connect(db).execute("SELECT COUNT(*) FROM fact_sales").fetchone()[0]
    assert len(df) == n_fact


def test_columns_and_no_nulls(exported):
    _, df = exported
    assert list(df.columns) == COLUMNS
    assert not df.isna().any().any()


def test_sales_total_matches_fact_table(exported):
    db, df = exported
    fact_total = sqlite3.connect(db).execute("SELECT SUM(sales_millions) FROM fact_sales").fetchone()[0]
    assert df["Sales (M units)"].sum() == pytest.approx(fact_total)


def test_regions_readable(exported):
    _, df = exported
    assert set(df["Region"]) == {"North America", "Europe", "Japan", "Rest of World"}
