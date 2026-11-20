# Data Dictionary: `vgsales.db` (SQLite star schema)

Grain of the fact table: **one row per game x region** (16,187 games x 4 regions = 64,748 rows).
Sales are in **millions of units** (physical retail, as tracked by VGChartz).

## fact_sales
| Column | Type | Description |
|---|---|---|
| game_key | INTEGER | FK -> dim_game. One title on one platform |
| platform_key | INTEGER | FK -> dim_platform |
| genre_key | INTEGER | FK -> dim_genre |
| publisher_key | INTEGER | FK -> dim_publisher |
| year_key | INTEGER | FK -> dim_year (release year) |
| region_key | INTEGER | FK -> dim_region |
| sales_millions | REAL | Units sold in that region, in millions |

## dim_game
| Column | Type | Description |
|---|---|---|
| game_key | INTEGER | Surrogate key |
| vgchartz_rank | INTEGER | Original global-sales rank from the source file |
| name | TEXT | Game title (the same title on two platforms is two rows) |

## dim_platform / dim_genre / dim_publisher
| Column | Type | Description |
|---|---|---|
| platform_key / genre_key / publisher_key | INTEGER | Surrogate key |
| platform / genre / publisher | TEXT | Name as in the source (31 platforms, 12 genres, 575 publishers) |

## dim_year
| Column | Type | Description |
|---|---|---|
| year_key | INTEGER | Surrogate key |
| year | INTEGER | Release year, 1980–2016 |
| decade | TEXT | e.g. `2000s` |

## dim_region
| Column | Type | Description |
|---|---|---|
| region_key | INTEGER | Surrogate key |
| region | TEXT | `NA`, `EU`, `JP`, `Other` |
| region_name | TEXT | North America, Europe, Japan, Rest of World |

## Cleaning rules (etl.py `clean`)
- Dropped 411 of 16,598 source rows: unknown release year (`N/A`), unknown publisher, or 2017+ placeholder records.
- `Global_Sales` is not stored, because it is derivable as the sum over regions. Tests confirm the fact total equals the sum of the source regional columns.
