import sqlite3
from pathlib import Path

import pandas as pd
import pytest

from etl import REGIONS, clean, run_etl

RAW = Path(__file__).resolve().parent.parent / "data" / "raw" / "vgsales.csv"


@pytest.fixture(scope="module")
def db(tmp_path_factory):
    path = tmp_path_factory.mktemp("db") / "vgsales.db"
    stats = run_etl(RAW, path)
    return path, stats


def test_clean_drops_unknown_year_and_publisher():
    df = clean(pd.read_csv(RAW))
    assert df["Year"].notna().all() and df["Publisher"].notna().all()
    assert df["Year"].dtype.kind == "i"
    assert 16000 < len(df) < 16598


def test_fact_rows_are_games_times_regions(db):
    path, stats = db
    con = sqlite3.connect(path)
    n_fact = con.execute("SELECT COUNT(*) FROM fact_sales").fetchone()[0]
    assert n_fact == stats["clean_rows"] * len(REGIONS)


def test_no_orphan_foreign_keys(db):
    con = sqlite3.connect(db[0])
    for dim, key in [("dim_game", "game_key"), ("dim_platform", "platform_key"), ("dim_genre", "genre_key"),
                     ("dim_publisher", "publisher_key"), ("dim_year", "year_key"), ("dim_region", "region_key")]:
        orphans = con.execute(f"SELECT COUNT(*) FROM fact_sales f LEFT JOIN {dim} d USING ({key}) "
                              f"WHERE d.{key} IS NULL").fetchone()[0]
        assert orphans == 0, dim


def test_fact_total_matches_source_regional_columns(db):
    path, _ = db
    df = clean(pd.read_csv(RAW))
    expected = df[["NA_Sales", "EU_Sales", "JP_Sales", "Other_Sales"]].to_numpy().sum()
    got = sqlite3.connect(path).execute("SELECT SUM(sales_millions) FROM fact_sales").fetchone()[0]
    assert abs(got - expected) < 1e-6


def test_wii_sports_na_sales(db):
    con = sqlite3.connect(db[0])
    v = con.execute("""SELECT f.sales_millions FROM fact_sales f JOIN dim_game g USING (game_key)
                       JOIN dim_region r USING (region_key) WHERE g.name='Wii Sports' AND r.region='NA'""").fetchone()[0]
    assert v == pytest.approx(41.49)


def test_all_queries_run_and_return_rows(db, tmp_path):
    from run_queries import run_all, load_queries
    res = run_all(db[0], tmp_path)
    assert set(res) == set(load_queries()) and len(res) == 5
    assert all(len(df) > 0 for df in res.values())
    top = res["top_publisher_per_region"]
    assert top[(top.region == "NA") & (top.rnk == 1)].publisher.item() == "Nintendo"


def test_model_evaluate_reports_three_regions_with_time_split():
    from model import evaluate, SPLIT_YEAR
    res = evaluate(RAW)
    assert list(res.region) == ["NA", "EU", "JP"]
    assert (res.mae_m >= 0).all() and res.r2.between(-5, 1).all()
    assert (res.test_titles > 1000).all() and SPLIT_YEAR == 2012
