
WITH source AS (
    SELECT
        game_pk,
        game_date,
        at_bat_number,
        pitch_number,

        pitcher AS pitcher_id,
        player_name,
        batter AS batter_id,

        pitch_type,
        description,
        events,

        release_speed,
        release_spin_rate,
        pfx_x,
        pfx_z,
        plate_x,
        plate_z,
        sz_top,
        sz_bot,

        stand AS batter_side,
        p_throws AS pitcher_hand,

        balls,
        strikes,
        launch_speed,
        launch_angle,

        estimated_woba_using_speedangle,

        year AS reporting_year,
        month AS reporting_month

    FROM read_parquet(
        '{{RAW_GLOB}}',
        hive_partitioning = true,
        union_by_name = true
    )
),

classified AS (
    SELECT
        *,

        -- Exclude nonstandard or unclassified records
        -- from our initial pitch metrics.
        CASE
            WHEN pitch_type IS NULL
              OR pitch_type IN ('UN', 'PO')
              OR description IN (
                  'automatic_ball',
                  'automatic_strike',
                  'pitchout'
              )
            THEN 0
            ELSE 1
        END AS is_eligible_pitch,

        CASE
            WHEN description IN (
                'swinging_strike',
                'swinging_strike_blocked',
                'foul',
                'foul_tip',
                'foul_bunt',
                'missed_bunt',
                'bunt_foul_tip',
                'hit_into_play'
            )
            THEN 1 ELSE 0
        END AS is_swing,

        CASE
            WHEN description IN (
                'swinging_strike',
                'swinging_strike_blocked',
                'missed_bunt'
            )
            THEN 1 ELSE 0
        END AS is_whiff,

        CASE
            WHEN description = 'called_strike'
            THEN 1 ELSE 0
        END AS is_called_strike,

        CASE
            WHEN events IN (
                'strikeout',
                'strikeout_double_play'
            )
            THEN 1 ELSE 0
        END AS is_strikeout,

        CASE
            WHEN events IN ('walk', 'intent_walk')
            THEN 1 ELSE 0
        END AS is_walk

    FROM source
)

SELECT
    *,
    CASE
        WHEN is_called_strike = 1 OR is_whiff = 1
        THEN 1 ELSE 0
    END AS is_csw

FROM classified;
