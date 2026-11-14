
WITH eligible AS (
    SELECT *
    FROM read_parquet('{{CURATED_FILE}}')
    WHERE is_eligible_pitch = 1
)

SELECT
    pitcher_id,
    MAX(player_name) AS player_name,

    COUNT(*) AS total_pitches,
    COUNT(DISTINCT game_pk) AS games,

    SUM(is_swing) AS swings,
    SUM(is_whiff) AS whiffs,
    SUM(is_called_strike) AS called_strikes,
    SUM(is_csw) AS csw_events,

    ROUND(AVG(release_speed), 1) AS avg_velocity,
    ROUND(AVG(release_spin_rate), 0) AS avg_spin,

    ROUND(
        100.0 * SUM(is_swing)
        / NULLIF(COUNT(*), 0),
        1
    ) AS swing_pct,

    ROUND(
        100.0 * SUM(is_whiff)
        / NULLIF(SUM(is_swing), 0),
        1
    ) AS whiff_pct,

    ROUND(
        100.0 * SUM(is_csw)
        / NULLIF(COUNT(*), 0),
        1
    ) AS csw_pct

FROM eligible
GROUP BY pitcher_id
ORDER BY total_pitches DESC;
