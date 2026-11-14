
from pathlib import Path

import duckdb
import pytest

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "curated"

OVERALL = DATA / "pitcher_overall.parquet"
SUMMARY = DATA / "pitcher_summary.parquet"


@pytest.fixture(scope="module")
def con():
    connection = duckdb.connect(":memory:")

    connection.execute(
        "CREATE TABLE overall AS "
        "SELECT * FROM read_parquet(?)",
        [str(OVERALL)],
    )

    connection.execute(
        "CREATE TABLE summary AS "
        "SELECT * FROM read_parquet(?)",
        [str(SUMMARY)],
    )

    yield connection
    connection.close()


def test_pitcher_count(con):
    count = con.execute(
        "SELECT COUNT(*) FROM overall"
    ).fetchone()[0]

    assert count == 552


def test_total_pitch_count(con):
    total = con.execute(
        "SELECT SUM(total_pitches) FROM overall"
    ).fetchone()[0]

    assert total == 115240


def test_unique_pitcher_ids(con):
    duplicates = con.execute("""
        SELECT COUNT(*) - COUNT(DISTINCT pitcher_id)
        FROM overall
    """).fetchone()[0]

    assert duplicates == 0


def test_unique_pitcher_pitch_types(con):
    duplicates = con.execute("""
        SELECT COUNT(*) - COUNT(DISTINCT (
            pitcher_id, pitch_type
        ))
        FROM summary
    """).fetchone()[0]

    assert duplicates == 0


def test_metric_ranges(con):
    invalid = con.execute("""
        SELECT COUNT(*)
        FROM overall
        WHERE
            swing_pct NOT BETWEEN 0 AND 100
            OR whiff_pct NOT BETWEEN 0 AND 100
            OR csw_pct NOT BETWEEN 0 AND 100
    """).fetchone()[0]

    assert invalid == 0


def test_aggregate_reconciliation(con):
    mismatches = con.execute("""
        WITH totals AS (
            SELECT
                pitcher_id,
                SUM(pitches) AS pitches,
                SUM(swings) AS swings,
                SUM(whiffs) AS whiffs,
                SUM(csw_events) AS csw_events
            FROM summary
            GROUP BY pitcher_id
        )
        SELECT COUNT(*)
        FROM overall o
        FULL OUTER JOIN totals t
            ON o.pitcher_id = t.pitcher_id
        WHERE
            o.pitcher_id IS NULL
            OR t.pitcher_id IS NULL
            OR o.total_pitches IS DISTINCT FROM t.pitches
            OR o.swings IS DISTINCT FROM t.swings
            OR o.whiffs IS DISTINCT FROM t.whiffs
            OR o.csw_events IS DISTINCT FROM t.csw_events
    """).fetchone()[0]

    assert mismatches == 0
