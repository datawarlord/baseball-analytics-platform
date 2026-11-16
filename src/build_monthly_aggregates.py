
import os
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]

OUTPUT_ROOT = Path(
    os.environ.get(
        "BASEBALL_CURATED_DIR",
        str(ROOT / "data" / "curated"),
    )
)

CURATED_ROOT = OUTPUT_ROOT / "pitch_details"

DATASETS = [
    (  
        "sql/04_pitcher_summary_monthly.sql",
        "pitcher_summary_monthly.parquet",
    ),
    (
        "sql/05_pitcher_overall_monthly.sql",
        "pitcher_overall_monthly.parquet",
    ),
]


def main():
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    curated_files = list(
        CURATED_ROOT.glob("year=*/month=*/pitches.parquet")
    )

    if not curated_files:
        raise FileNotFoundError(
            "No partitioned curated pitch data found"
        )

    curated_glob = (
        CURATED_ROOT / "year=*/month=*/*.parquet"
    ).as_posix().replace("'", "''")

    with duckdb.connect(":memory:") as con:
        for sql_path, output_name in DATASETS:
            sql = (
                ROOT / sql_path
            ).read_text(encoding="utf-8")

            sql = sql.replace(
                "{{CURATED_GLOB}}",
                curated_glob,
            )

            output_file = OUTPUT_ROOT / output_name
            temp_file = OUTPUT_ROOT / (
                output_name + ".tmp"
            )

            con.execute(
                "CREATE OR REPLACE TEMP TABLE result AS "
                + sql
            )

            rows = con.execute(
                "SELECT COUNT(*) FROM result"
            ).fetchone()[0]

            if rows == 0:
                raise ValueError(
                    f"No rows produced for {output_name}"
                )

            try:
                con.execute(
                    "COPY result TO ? "
                    "(FORMAT PARQUET, COMPRESSION ZSTD)",
                    [str(temp_file)],
                )

                temp_file.replace(output_file)
            finally:
                temp_file.unlink(missing_ok=True)

            print(
                f"Created {output_name}: {rows:,} rows"
            )


if __name__ == "__main__":
    main()
