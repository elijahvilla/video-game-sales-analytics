"""Forecast regional sales for new titles from platform, genre, publisher, and release year.

Time-based split: train on titles released <= 2012, test on 2013-2016 (simulates forecasting new releases).
Target: log1p(regional sales, millions). Metrics reported on the original scale (millions of units).
Compared against a naive baseline (training median per region).

Usage: python model.py   -> prints metrics and writes results/model_metrics.csv
"""
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from etl import clean

ROOT = Path(__file__).resolve().parent
TARGETS = {"NA": "NA_Sales", "EU": "EU_Sales", "JP": "JP_Sales"}
CATS = ["Platform", "Genre", "Publisher"]
SPLIT_YEAR = 2012
TOP_PUBLISHERS = 40


def features(df: pd.DataFrame, top_publishers) -> pd.DataFrame:
    X = df[CATS + ["Year"]].copy()
    X["Publisher"] = X["Publisher"].where(X["Publisher"].isin(top_publishers), "Other")
    return X


def build_model() -> Pipeline:
    pre = ColumnTransformer([("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CATS)],
                            remainder="passthrough")
    return Pipeline([("pre", pre), ("gbm", HistGradientBoostingRegressor(max_iter=300, learning_rate=0.05,
                                                                          random_state=42))])


def evaluate(raw_csv=ROOT / "data" / "raw" / "vgsales.csv") -> pd.DataFrame:
    df = clean(pd.read_csv(raw_csv))
    train, test = df[df.Year <= SPLIT_YEAR], df[df.Year > SPLIT_YEAR]
    top = train.groupby("Publisher")["Global_Sales"].sum().nlargest(TOP_PUBLISHERS).index
    Xtr, Xte = features(train, top), features(test, top)
    rows = []
    for region, col in TARGETS.items():
        m = build_model().fit(Xtr, np.log1p(train[col]))
        pred = np.expm1(m.predict(Xte)).clip(min=0)
        base = np.full(len(test), train[col].median())
        rows.append({"region": region, "train_titles": len(train), "test_titles": len(test),
                     "r2": r2_score(test[col], pred), "mae_m": mean_absolute_error(test[col], pred),
                     "baseline_mae_m": mean_absolute_error(test[col], base),
                     "mae_improvement_pct": 100 * (1 - mean_absolute_error(test[col], pred)
                                                   / mean_absolute_error(test[col], base))})
    return pd.DataFrame(rows)


if __name__ == "__main__":
    res = evaluate()
    (ROOT / "results").mkdir(exist_ok=True)
    res.round(4).to_csv(ROOT / "results" / "model_metrics.csv", index=False)
    print(res.round(3).to_string(index=False))
