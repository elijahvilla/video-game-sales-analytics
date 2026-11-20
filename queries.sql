-- name: top_publisher_per_region
-- Q1. Which publisher leads each region, and what share of that region's sales does it hold? (CTE + RANK + window SUM)
WITH pub_region AS (
    SELECT r.region, p.publisher, SUM(f.sales_millions) AS sales
    FROM fact_sales f
    JOIN dim_region r USING (region_key)
    JOIN dim_publisher p USING (publisher_key)
    GROUP BY r.region, p.publisher
), ranked AS (
    SELECT region, publisher, sales,
           RANK() OVER (PARTITION BY region ORDER BY sales DESC) AS rnk,
           sales / SUM(sales) OVER (PARTITION BY region) AS share
    FROM pub_region
)
SELECT region, rnk, publisher, ROUND(sales, 1) AS sales_m, ROUND(100 * share, 1) AS share_pct
FROM ranked WHERE rnk <= 3 ORDER BY region, rnk;

-- name: genre_share_by_decade
-- Q2. How has each genre's share of global sales shifted by decade? (CTE + window SUM)
WITH g AS (
    SELECT y.decade, ge.genre, SUM(f.sales_millions) AS sales
    FROM fact_sales f JOIN dim_year y USING (year_key) JOIN dim_genre ge USING (genre_key)
    GROUP BY y.decade, ge.genre
)
SELECT decade, genre, ROUND(sales, 1) AS sales_m,
       ROUND(100.0 * sales / SUM(sales) OVER (PARTITION BY decade), 1) AS share_pct
FROM g ORDER BY decade, share_pct DESC;

-- name: platform_peak_year
-- Q3. In which year did each major platform peak, and how long was its sales life? (CTE + ROW_NUMBER + MIN/MAX)
WITH py AS (
    SELECT pl.platform, y.year, SUM(f.sales_millions) AS sales
    FROM fact_sales f JOIN dim_platform pl USING (platform_key) JOIN dim_year y USING (year_key)
    GROUP BY pl.platform, y.year
), life AS (
    SELECT platform, SUM(sales) AS lifetime, MIN(year) AS first_year, MAX(year) AS last_year
    FROM py GROUP BY platform HAVING SUM(sales) >= 100
), peak AS (
    SELECT platform, year, sales, ROW_NUMBER() OVER (PARTITION BY platform ORDER BY sales DESC) AS rn FROM py
)
SELECT l.platform, ROUND(l.lifetime, 1) AS lifetime_m, p.year AS peak_year, ROUND(p.sales, 1) AS peak_year_m,
       l.first_year, l.last_year, l.last_year - l.first_year + 1 AS active_years
FROM life l JOIN peak p ON p.platform = l.platform AND p.rn = 1
ORDER BY l.lifetime DESC;

-- name: jp_vs_na_genre_preference
-- Q4. Which genres over- or under-index in Japan vs. North America? (CTE + conditional aggregation)
WITH s AS (
    SELECT ge.genre,
           SUM(CASE WHEN r.region = 'JP' THEN f.sales_millions END) AS jp,
           SUM(CASE WHEN r.region = 'NA' THEN f.sales_millions END) AS na
    FROM fact_sales f JOIN dim_genre ge USING (genre_key) JOIN dim_region r USING (region_key)
    GROUP BY ge.genre
), shares AS (
    SELECT genre, jp, na, jp / SUM(jp) OVER () AS jp_share, na / SUM(na) OVER () AS na_share FROM s
)
SELECT genre, ROUND(100 * jp_share, 1) AS jp_share_pct, ROUND(100 * na_share, 1) AS na_share_pct,
       ROUND(jp_share / na_share, 2) AS jp_index
FROM shares ORDER BY jp_index DESC;

-- name: market_yoy_growth
-- Q5. Year-over-year growth of the global market, with a 3-year moving average. (CTE + LAG + AVG OVER)
WITH yr AS (
    SELECT y.year, SUM(f.sales_millions) AS sales
    FROM fact_sales f JOIN dim_year y USING (year_key) GROUP BY y.year
)
SELECT year, ROUND(sales, 1) AS sales_m,
       ROUND(100.0 * (sales - LAG(sales) OVER (ORDER BY year)) / LAG(sales) OVER (ORDER BY year), 1) AS yoy_pct,
       ROUND(AVG(sales) OVER (ORDER BY year ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 1) AS moving_avg_3y
FROM yr WHERE year >= 1995 ORDER BY year;
