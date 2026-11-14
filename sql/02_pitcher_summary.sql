
WITH eligible AS (
    SELECT *
    FROM read_parquet('{{CURATED_FILE}}')
    WHERE is_eligible_pitch = 1
),

pitcher_totals AS (
    SELECT
        pitcher_id,
        COUNT(*) AS total_pitches
    FROM eligible
    GROUP BY pitcher_id
),

pitcher_pitch_type AS (
    SELECT
        pitcher_id,
        player_name,
        pitch_type,

        COUNT(*) AS pitches,
        ROUND(AVG(release_speed), 1) AS avg_velocity,
        ROUND(AVG(release_spin_rate), 0) AS avg_spin,

        SUM(is_swing) AS swings,
        SUM(is_whiff) AS whiffs,
        SUM(is_csw) AS csw_events

    FROM eligible
    GROUP BY
        pitcher_id,
        player_name,
        pitch_type
),

league_pitch_type AS (
    SELECT
        pitch_type,

        COUNT(*) AS league_pitches,
        SUM(is_swing) AS league_swings,
        SUM(is_whiff) AS league_whiffs,
        SUM(is_csw) AS league_csw_events

    FROM eligible
    GROUP BY pitch_type
)

SELECT
    p.pitcher_id,
    p.player_name,
    p.pitch_type,

    p.pitches,

    ROUND(
        100.0 * p.pitches
        / NULLIF(t.total_pitches, 0),
        1
    ) AS usage_pct,

    p.avg_velocity,
    p.avg_spin,
    p.swings,
    p.whiffs,
    p.csw_events,

    ROUND(
        100.0 * p.whiffs
        / NULLIF(p.swings, 0),
        1
    ) AS whiff_pct,

    ROUND(
        100.0 * p.csw_events
        / NULLIF(p.pitches, 0),
        1
    ) AS csw_pct,

    ROUND(
        100.0 * l.league_whiffs
        / NULLIF(l.league_swings, 0),
        1
    ) AS league_whiff_pct,

    ROUND(
        100.0 * l.league_csw_events
        / NULLIF(l.league_pitches, 0),
        1
    ) AS league_csw_pct

FROM pitcher_pitch_type p

JOIN pitcher_totals t
    ON p.pitcher_id = t.pitcher_id

JOIN league_pitch_type l
    ON p.pitch_type = l.pitch_type

ORDER BY
    p.player_name,
    p.pitches DESC;
