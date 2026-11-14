
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = ROOT / "data/curated/pitch_details.parquet"
OUTPUT_FILE = ROOT / "data/curated/pitcher_summary.parquet"
SQL_FILE = ROOT / "sql/02_pitcher_summary.sql"


def main():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(INPUT_FILE)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    sql = SQL_FILE.read_text(encoding="utf-8")

    input_path = INPUT_FILE.as_posix().replace("'", "''")
    sql = sql.replace("{{CURATED_FILE}}", input_path)

    with duckdb.connect(":memory:") as con:
        con.execute("CREATE TEMP TABLE summary AS " + sql)

        results = con.execute("""
            SELECT
                COUNT(*) AS rows,
                COUNT(DISTINCT pitcher_id) AS pitchers,
                COUNT(DISTINCT pitch_type) AS pitch_types,
                SUM(pitches) AS pitches
            FROM summary
        """).fetchone()

        duplicates = con.execute("""
            SELECT COUNT(*) - COUNT(DISTINCT (
                pitcher_id, pitch_type
            ))
            FROM summary
        """).fetchone()[0]

        if duplicates:
            raise ValueError(
                f"Duplicate pitcher/pitch-type keys: {duplicates}"
            )

        if results[3] != 115240:
            raise ValueError(
                f"Unexpected eligible pitch total: {results[3]}"
            )

        con.execute(
            "COPY summary TO ? "
            "(FORMAT PARQUET, COMPRESSION ZSTD)",
            [str(OUTPUT_FILE)]
        )

    print("\n=== PITCHER SUMMARY ===")
    print(f"Rows: {results[0]:,}")
    print(f"Pitchers: {results[1]:,}")
    print(f"Pitch types: {results[2]:,}")
    print(f"Eligible pitches: {results[3]:,}")
    print(f"Duplicate keys: {duplicates}")
    print(f"Output: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
