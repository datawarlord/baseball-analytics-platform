
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
OVERALL = ROOT / "data/curated/pitcher_overall.parquet"
BY_TYPE = ROOT / "data/curated/pitcher_summary.parquet"

with duckdb.connect(":memory:") as con:
    results = con.execute("""
        WITH by_type AS (
            SELECT
                pitcher_id,
                SUM(pitches) AS pitches,
                SUM(swings) AS swings,
                SUM(whiffs) AS whiffs,
                SUM(csw_events) AS csw_events
            FROM read_parquet(?)
            GROUP BY pitcher_id
        )
        SELECT
            COUNT(*) AS mismatches
        FROM read_parquet(?) o
        FULL OUTER JOIN by_type t
            ON o.pitcher_id = t.pitcher_id
        WHERE
            o.pitcher_id IS NULL
            OR t.pitcher_id IS NULL
            OR o.total_pitches IS DISTINCT FROM t.pitches
            OR o.swings IS DISTINCT FROM t.swings
            OR o.whiffs IS DISTINCT FROM t.whiffs
            OR o.csw_events IS DISTINCT FROM t.csw_events
    """, [str(BY_TYPE), str(OVERALL)]).fetchone()

    mismatches = results[0]

    print(f"Pitcher aggregate mismatches: {mismatches}")

    assert mismatches == 0, (
        f"Found {mismatches} mismatched pitcher aggregates"
    )

    print("Validation passed!")
