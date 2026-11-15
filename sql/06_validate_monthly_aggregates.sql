-- Compare monthly pitch counts across both aggregates
WITH summary AS (
    SELECT
        reporting_year,
        reporting_month,
        SUM(pitches) AS summary_pitches,
        SUM(swings) AS summary_swings,
        SUM(whiffs) AS summary_whiffs,
        SUM(csw_events) AS summary_csw
    FROM read_parquet(
        'C:/Users/josep/src/baseball-analytics-platform/data/curated/pitcher_summary_monthly.parquet'
    )
    GROUP BY 1, 2
),
overall AS (
    SELECT
        reporting_year,
        reporting_month,
        SUM(total_pitches) AS overall_pitches,
        SUM(swings) AS overall_swings,
        SUM(whiffs) AS overall_whiffs,
        SUM(csw_events) AS overall_csw
    FROM read_parquet(
        'C:/Users/josep/src/baseball-analytics-platform/data/curated/pitcher_overall_monthly.parquet'
    )
    GROUP BY 1, 2
)
SELECT
    o.reporting_year,
    o.reporting_month,
    o.overall_pitches,
    s.summary_pitches,
    o.overall_swings,
    s.summary_swings,
    o.overall_whiffs,
    s.summary_whiffs,
    o.overall_csw,
    s.summary_csw
FROM overall o
JOIN summary s
    USING (reporting_year, reporting_month)
ORDER BY 1, 2;

SELECT
    COUNT(*) AS rows,
    COUNT(DISTINCT (
        reporting_year,
        reporting_month,
        pitcher_id,
        pitch_type
    )) AS unique_keys
FROM read_parquet(
    'C:/Users/josep/src/baseball-analytics-platform/data/curated/pitcher_summary_monthly.parquet'
);