"""Convert vgsales_tableau.csv into a Tableau .hyper extract (Tableau Public requires extracts).

Usage: python tableau/make_extract.py
Needs: pip install tableauhyperapi
"""
from pathlib import Path

import pandas as pd
from tableauhyperapi import (Connection, CreateMode, HyperProcess, Inserter, SqlType, TableDefinition,
                             TableName, Telemetry)

HERE = Path(__file__).resolve().parent
CSV = HERE / "vgsales_tableau.csv"
HYPER = HERE / "vgsales_tableau.hyper"

TABLE = TableDefinition(TableName("Extract", "Extract"), [
    TableDefinition.Column("Game", SqlType.text()),
    TableDefinition.Column("Platform", SqlType.text()),
    TableDefinition.Column("Genre", SqlType.text()),
    TableDefinition.Column("Publisher", SqlType.text()),
    TableDefinition.Column("Year", SqlType.big_int()),
    TableDefinition.Column("Decade", SqlType.text()),
    TableDefinition.Column("Region", SqlType.text()),
    TableDefinition.Column("Sales (M units)", SqlType.double()),
])


def main():
    df = pd.read_csv(CSV)
    rows = [(r.Game, r.Platform, r.Genre, r.Publisher, int(r.Year), r.Decade, r.Region, float(r[7]))
            for r in df.itertuples(index=False)]
    with HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as hyper:
        with Connection(hyper.endpoint, HYPER, CreateMode.CREATE_AND_REPLACE) as con:
            con.catalog.create_schema("Extract")
            con.catalog.create_table(TABLE)
            with Inserter(con, TABLE) as ins:
                ins.add_rows(rows)
                ins.execute()
            n = con.execute_scalar_query('SELECT COUNT(*) FROM "Extract"."Extract"')
            total = con.execute_scalar_query('SELECT SUM("Sales (M units)") FROM "Extract"."Extract"')
    assert n == len(df), (n, len(df))
    print(f"wrote {HYPER.name}: {n:,} rows, {total:,.1f}M units")


if __name__ == "__main__":
    main()
