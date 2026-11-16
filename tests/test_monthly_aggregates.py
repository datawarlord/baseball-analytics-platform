
from pathlib import Path

import duckdb
import pytest
import os

ROOT = Path(__file__).resolve().parents[1]
CURATED = Path(
    os.environ.get(
        "BASEBALL_CURATED_DIR",
        str(ROOT / "data" / "curated"),
    )
)
SUMMARY = CURATED / "pitcher_summary_monthly.parquet"
OVERALL = CURATED / "pitcher_overall_monthly.parquet"
DETAILS = CURATED / "pitch_details"



@pytest.fixture(scope="module")
def con():
    required_files = [SUMMARY, OVERALL]

    for file in required_files:
        if not file.exists():
            pytest.fail(f"Missing required dataset: {file}")

    detail_files = list(
        DETAILS.glob("year=*/month=*/pitches.parquet")
    )

    if not detail_files:
        pytest.fail("No curated monthly pitch partitions found")

    connection = duckdb.connect(":memory:")

    # Escape paths before embedding them in SQL literals.
    summary_path = SUMMARY.as_posix().replace("'", "''")
    overall_path = OVERALL.as_posix().replace("'", "''")
    details_path = (
        DETAILS / "year=*/month=*/*.parquet"
    ).as_posix().replace("'", "''")

    connection.execute(f"""
        CREATE VIEW summary AS
        SELECT *
        FROM read_parquet('{summary_path}')
    """)

    connection.execute(f"""
        CREATE VIEW overall AS
        SELECT *
        FROM read_parquet('{overall_path}')
    """)

    connection.execute(f"""
        CREATE VIEW details AS
        SELECT *
        FROM read_parquet(
            '{details_path}',
            hive_partitioning = true
        )
    """)

    yield connection
    connection.close()


def test_monthly_summary_unique_keys(con):
    duplicates = con.execute("""
        SELECT
            COUNT(*) - COUNT(DISTINCT (
                reporting_year,
                reporting_month,
                pitcher_id,
                pitch_type
            ))
        FROM summary
    """).fetchone()[0]

    assert duplicates == 0


def test_monthly_overall_unique_keys(con):
    duplicates = con.execute("""
        SELECT
            COUNT(*) - COUNT(DISTINCT (
                reporting_year,
                reporting_month,
                pitcher_id
            ))
        FROM overall
    """).fetchone()[0]

    assert duplicates == 0


def test_monthly_counts_reconcile(con):
    mismatches = con.execute("""
        WITH s AS (
            SELECT
                reporting_year,
                reporting_month,
                SUM(pitches) AS pitches,
                SUM(swings) AS swings,
                SUM(whiffs) AS whiffs,
                SUM(csw_events) AS csw
            FROM summary
            GROUP BY 1, 2
        ),
        o AS (
            SELECT
                reporting_year,
                reporting_month,
                SUM(total_pitches) AS pitches,
                SUM(swings) AS swings,
                SUM(whiffs) AS whiffs,
                SUM(csw_events) AS csw
            FROM overall
            GROUP BY 1, 2
        )
        SELECT COUNT(*)
        FROM s
        FULL OUTER JOIN o USING (
            reporting_year, reporting_month
        )
        WHERE
            s.pitches IS DISTINCT FROM o.pitches
            OR s.swings IS DISTINCT FROM o.swings
            OR s.whiffs IS DISTINCT FROM o.whiffs
            OR s.csw IS DISTINCT FROM o.csw
    """).fetchone()[0]

    assert mismatches == 0


def test_monthly_overall_matches_details(con):
    mismatches = con.execute("""
        WITH d AS (
            SELECT
                reporting_year,
                reporting_month,
                pitcher_id,
                COUNT(*) AS pitches,
                SUM(is_swing) AS swings,
                SUM(is_whiff) AS whiffs,
                SUM(is_csw) AS csw
            FROM details
            WHERE is_eligible_pitch = 1
            GROUP BY 1, 2, 3
        )
        SELECT COUNT(*)
        FROM d
        FULL OUTER JOIN overall o
            USING (
                reporting_year,
                reporting_month,
                pitcher_id
            )
        WHERE
            d.pitches IS DISTINCT FROM o.total_pitches
            OR d.swings IS DISTINCT FROM o.swings
            OR d.whiffs IS DISTINCT FROM o.whiffs
            OR d.csw IS DISTINCT FROM o.csw_events
    """).fetchone()[0]

    assert mismatches == 0


def test_monthly_metric_ranges(con):
    invalid = con.execute("""
        SELECT COUNT(*)
        FROM overall
        WHERE
            swing_pct NOT BETWEEN 0 AND 100
            OR whiff_pct NOT BETWEEN 0 AND 100
            OR csw_pct NOT BETWEEN 0 AND 100
    """).fetchone()[0]

    assert invalid == 0


def test_multiple_months_present(con):
    months = con.execute("""
        SELECT COUNT(DISTINCT (
            reporting_year, reporting_month
        ))
        FROM overall
    """).fetchone()[0]

    assert months >= 2
