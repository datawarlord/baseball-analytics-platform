
from pathlib import Path

import duckdb

PROJECT_ROOT = Path(__file__).resolve().parents[1]

RAW_ROOT = PROJECT_ROOT / "data/raw/statcast"
CURATED_ROOT = PROJECT_ROOT / "data/curated/pitch_details"

SQL_FILE = PROJECT_ROOT / "sql/01_curate_pitches.sql"


def main():
    raw_files = sorted(RAW_ROOT.glob(
        "year=*/month=*/pitches.parquet"
    ))

    if not raw_files:
        raise FileNotFoundError(
            f"No raw Statcast partitions found in {RAW_ROOT}"
        )

    CURATED_ROOT.mkdir(parents=True, exist_ok=True)

    sql = SQL_FILE.read_text(encoding="utf-8")

    raw_glob = (
        RAW_ROOT / "year=*/month=*/*.parquet"
    ).as_posix().replace("'", "''")

    sql = sql.replace("{{RAW_GLOB}}", raw_glob)

    with duckdb.connect(":memory:") as con:
        con.execute(
            "CREATE TEMP TABLE curated AS " + sql
        )

        stats = con.execute("""
            SELECT
                COUNT(*) AS total_rows,
                SUM(is_eligible_pitch) AS eligible_pitches,
                COUNT(*) - COUNT(DISTINCT (
                    game_pk,
                    at_bat_number,
                    pitch_number
                )) AS duplicate_keys
            FROM curated
        """).fetchone()

        total_rows, eligible, duplicates = stats

        if total_rows == 0:
            raise ValueError("Curated table is empty")

        if duplicates:
            raise ValueError(
                f"Found {duplicates} duplicate pitch keys"
            )

        months = con.execute("""
            SELECT
                reporting_year,
                reporting_month,
                COUNT(*) AS pitches
            FROM curated
            GROUP BY 1, 2
            ORDER BY 1, 2
        """).fetchall()

        for year, month, count in months:
            output_dir = (
                CURATED_ROOT
                / f"year={year}"
                / f"month={int(month):02d}"
            )

            output_dir.mkdir(
                parents=True,
                exist_ok=True
            )

            output_file = output_dir / "pitches.parquet"
            temp_file = output_dir / "pitches.tmp.parquet"

            try:
                con.execute("""
                    COPY (
                        SELECT *
                        FROM curated
                        WHERE reporting_year = ?
                          AND reporting_month = ?
                    )
                    TO ?
                    (FORMAT PARQUET, COMPRESSION ZSTD)
                """, [year, month, str(temp_file)])

                temp_file.replace(output_file)
            finally:
                temp_file.unlink(missing_ok=True)

            print(
                f"{year}-{int(month):02d}: "
                f"{count:,} pitches -> {output_file}"
            )

    print(f"\nTotal records: {total_rows:,}")
    print(f"Eligible pitches: {eligible:,}")
    print(f"Duplicate keys: {duplicates:,}")
    print("Partitioned transformation complete!")


if __name__ == "__main__":
    main()
