SELECT
    year,
    month,
    COUNT(*) AS eligible_pitches,
    SUM(is_swing) AS swings,
    SUM(is_whiff) AS whiffs,
    SUM(is_csw) AS csw_events
FROM read_parquet(
    'C:/Users/josep/src/baseball-analytics-platform/data/curated/pitch_details/year=*/month=*/*.parquet',
    hive_partitioning = true
)
WHERE is_eligible_pitch = 1
GROUP BY year, month
ORDER BY year, month;