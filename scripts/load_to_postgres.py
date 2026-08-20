"""
Data Analyst Job Market Intelligence: Skill, Experience & Salary Analytics — India

PostgreSQL star-schema loader.

Inputs
------
data/processed/job_postings_clean.csv
data/processed/job_skills_bridge.csv
sql/schema.sql
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values


PROJECT_ROOT = Path(__file__).resolve().parents[1]

JOBS_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "job_postings_clean.csv"
)

SKILLS_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "job_skills_bridge.csv"
)

SCHEMA_FILE = (
    PROJECT_ROOT
    / "sql"
    / "schema.sql"
)

EXPECTED_JOB_ROWS = 4_035
EXPECTED_SKILL_ROWS = 6_213
EXPECTED_SKILLS = 44
EXPECTED_SALARY_ROWS = 110


def env(
    name: str,
    default: str | None = None,
) -> str:
    value = os.getenv(
        name,
        default,
    )

    if value is None or not str(value).strip():
        raise RuntimeError(
            f"Set environment variable {name}."
        )

    return str(value)


def get_connection():
    return psycopg2.connect(
        host=env(
            "PGHOST",
            "localhost",
        ),
        port=env(
            "PGPORT",
            "5432",
        ),
        dbname=env(
            "PGDATABASE",
            "job_market",
        ),
        user=env(
            "PGUSER",
            "postgres",
        ),
        password=env(
            "PGPASSWORD",
        ),
    )


def to_none(
    value: Any,
) -> Any:
    try:
        if pd.isna(value):
            return None
    except Exception:
        pass

    if hasattr(
        value,
        "item",
    ):
        try:
            return value.item()
        except Exception:
            pass

    return value


def to_bool(
    value: Any,
) -> bool:
    if isinstance(
        value,
        bool,
    ):
        return value

    try:
        if pd.isna(value):
            return False
    except Exception:
        pass

    return str(value).strip().lower() in {
        "1",
        "1.0",
        "true",
        "yes",
        "y",
    }


def to_optional_bool(
    value: Any,
) -> bool | None:
    try:
        if pd.isna(value):
            return None
    except Exception:
        pass

    return to_bool(value)


def validate_inputs(
    jobs: pd.DataFrame,
    skills: pd.DataFrame,
) -> None:
    required_job_columns = {
        "job_id",
        "source",
        "source_family",
        "source_provider",
        "title",
        "company_name",
        "location_name",
        "city",
        "state",
        "location_scope",
        "role_family",
        "work_mode",
        "description",
        "posted_date",
        "is_recent_90d",
        "is_complete_week",
        "experience_min_years",
        "experience_max_years",
        "experience_band",
        "salary_min_source",
        "salary_max_source",
        "salary_min",
        "salary_max",
        "salary_midpoint",
        "salary_is_predicted",
        "has_salary_source",
        "salary_analysis_eligible",
        "salary_normalization_status",
        "salary_text_evidence",
        "skill_count",
        "has_extracted_skill",
        "contract_type",
        "contract_time",
        "redirect_url",
    }

    required_skill_columns = {
        "job_id",
        "skill",
        "skill_category",
    }

    missing_job_columns = sorted(
        required_job_columns
        - set(jobs.columns)
    )

    if missing_job_columns:
        raise RuntimeError(
            "Processed jobs are missing required columns: "
            + ", ".join(
                missing_job_columns
            )
        )

    missing_skill_columns = sorted(
        required_skill_columns
        - set(skills.columns)
    )

    if missing_skill_columns:
        raise RuntimeError(
            "Skill bridge is missing required columns: "
            + ", ".join(
                missing_skill_columns
            )
        )

    if len(jobs) != EXPECTED_JOB_ROWS:
        raise RuntimeError(
            f"Expected {EXPECTED_JOB_ROWS:,} processed jobs "
            f"but found {len(jobs):,}."
        )

    if (
        jobs["job_id"]
        .astype("string")
        .duplicated()
        .any()
    ):
        raise RuntimeError(
            "Processed jobs contain repeated job_id values."
        )

    if len(skills) != EXPECTED_SKILL_ROWS:
        raise RuntimeError(
            f"Expected {EXPECTED_SKILL_ROWS:,} job-skill rows "
            f"but found {len(skills):,}."
        )

    if (
        skills["skill"].nunique()
        != EXPECTED_SKILLS
    ):
        raise RuntimeError(
            "Skill count does not match the analytical dataset."
        )

    if skills.duplicated(
        subset=[
            "job_id",
            "skill",
        ]
    ).any():
        raise RuntimeError(
            "Skill bridge contains repeated job-skill pairs."
        )

    job_ids = set(
        jobs["job_id"]
        .astype(str)
    )

    skill_job_ids = set(
        skills["job_id"]
        .astype(str)
    )

    if not skill_job_ids.issubset(
        job_ids
    ):
        raise RuntimeError(
            "Skill bridge contains job identifiers "
            "that are not present in processed jobs."
        )

    salary_eligible = (
        jobs[
            "salary_analysis_eligible"
        ]
        .map(to_bool)
    )

    if int(
        salary_eligible.sum()
    ) != EXPECTED_SALARY_ROWS:
        raise RuntimeError(
            f"Expected {EXPECTED_SALARY_ROWS:,} salary-analysis rows "
            f"but found {int(salary_eligible.sum()):,}."
        )

    salary_fields = jobs.loc[
        salary_eligible,
        [
            "salary_min",
            "salary_max",
            "salary_midpoint",
        ],
    ].apply(
        pd.to_numeric,
        errors="coerce",
    )

    if (
        salary_fields
        .isna()
        .any()
        .any()
    ):
        raise RuntimeError(
            "Salary-analysis rows contain missing salary values."
        )

    if (
        salary_fields["salary_min"]
        .le(0)
        .any()
        or salary_fields["salary_max"]
        .le(0)
        .any()
    ):
        raise RuntimeError(
            "Salary-analysis rows contain non-positive salary values."
        )

    if (
        salary_fields["salary_max"]
        < salary_fields["salary_min"]
    ).any():
        raise RuntimeError(
            "Salary-analysis rows contain invalid salary ranges."
        )


def run_schema(
    cur,
) -> None:
    sql_text = SCHEMA_FILE.read_text(
        encoding="utf-8"
    )

    cur.execute(
        sql_text
    )


def load_dimensions(
    cur,
    jobs: pd.DataFrame,
    skills: pd.DataFrame,
) -> None:
    roles = sorted(
        jobs["role_family"]
        .fillna("Other Analyst")
        .astype(str)
        .unique()
        .tolist()
    )

    execute_values(
        cur,
        """
        INSERT INTO job_market.dim_role (
            role_family
        )
        VALUES %s
        ON CONFLICT (role_family) DO NOTHING
        """,
        [
            (value,)
            for value in roles
        ],
    )

    companies = sorted(
        jobs["company_name"]
        .fillna("Unknown Company")
        .astype(str)
        .str.strip()
        .replace(
            "",
            "Unknown Company",
        )
        .unique()
        .tolist()
    )

    execute_values(
        cur,
        """
        INSERT INTO job_market.dim_company (
            company_name
        )
        VALUES %s
        ON CONFLICT (company_name) DO NOTHING
        """,
        [
            (value,)
            for value in companies
        ],
    )

    locations = (
        jobs[
            [
                "city",
                "state",
                "location_name",
                "location_scope",
            ]
        ]
        .fillna(
            {
                "city": "Unknown",
                "state": "Unknown",
                "location_name": "Unknown",
                "location_scope": "Unknown",
            }
        )
        .drop_duplicates()
    )

    execute_values(
        cur,
        """
        INSERT INTO job_market.dim_location (
            city,
            state,
            location_name,
            location_scope
        )
        VALUES %s
        ON CONFLICT (
            city,
            state,
            location_name,
            location_scope
        ) DO NOTHING
        """,
        [
            (
                str(row.city),
                str(row.state),
                str(row.location_name),
                str(row.location_scope),
            )
            for row in locations.itertuples(
                index=False
            )
        ],
        page_size=1000,
    )

    posted_dates = pd.to_datetime(
        jobs["posted_date"],
        errors="raise",
    )

    dates = pd.DataFrame(
        {
            "date_key": (
                posted_dates
                .dt.date
            ),
        }
    ).drop_duplicates()

    date_series = pd.to_datetime(
        dates["date_key"]
    )

    dates["calendar_year"] = (
        date_series.dt.year
    )

    dates["calendar_month"] = (
        date_series.dt.month
    )

    dates["month_name"] = (
        date_series.dt.month_name()
    )

    dates["year_month"] = (
        date_series.dt.strftime(
            "%Y-%m"
        )
    )

    dates["week_start"] = (
        date_series
        - pd.to_timedelta(
            date_series.dt.weekday,
            unit="D",
        )
    ).dt.date

    dates["day_of_week"] = (
        date_series.dt.weekday
    )

    dates["day_name"] = (
        date_series.dt.day_name()
    )

    execute_values(
        cur,
        """
        INSERT INTO job_market.dim_date (
            date_key,
            calendar_year,
            calendar_month,
            month_name,
            year_month,
            week_start,
            day_of_week,
            day_name
        )
        VALUES %s
        ON CONFLICT (date_key) DO NOTHING
        """,
        [
            tuple(row)
            for row in dates[
                [
                    "date_key",
                    "calendar_year",
                    "calendar_month",
                    "month_name",
                    "year_month",
                    "week_start",
                    "day_of_week",
                    "day_name",
                ]
            ].itertuples(
                index=False,
                name=None,
            )
        ],
        page_size=1000,
    )

    skill_dim = (
        skills[
            [
                "skill",
                "skill_category",
            ]
        ]
        .drop_duplicates()
        .sort_values(
            "skill"
        )
    )

    execute_values(
        cur,
        """
        INSERT INTO job_market.dim_skill (
            skill,
            skill_category
        )
        VALUES %s
        ON CONFLICT (skill) DO NOTHING
        """,
        [
            (
                str(row.skill),
                str(row.skill_category),
            )
            for row in skill_dim.itertuples(
                index=False
            )
        ],
        page_size=1000,
    )


def lookup_map(
    cur,
    table: str,
    key_column: str,
    value_columns: list[str],
) -> dict[tuple[str, ...], Any]:
    selected = ", ".join(
        [
            key_column,
            *value_columns,
        ]
    )

    cur.execute(
        f"""
        SELECT {selected}
        FROM job_market.{table}
        """
    )

    mapping: dict[
        tuple[str, ...],
        Any,
    ] = {}

    for row in cur.fetchall():
        key = row[0]
        values = row[1:]

        mapping[
            tuple(
                ""
                if value is None
                else str(value)
                for value in values
            )
        ] = key

    return mapping


def load_fact_jobs(
    cur,
    jobs: pd.DataFrame,
) -> None:
    role_map = lookup_map(
        cur,
        "dim_role",
        "role_key",
        [
            "role_family",
        ],
    )

    company_map = lookup_map(
        cur,
        "dim_company",
        "company_key",
        [
            "company_name",
        ],
    )

    location_map = lookup_map(
        cur,
        "dim_location",
        "location_key",
        [
            "city",
            "state",
            "location_name",
            "location_scope",
        ],
    )

    fact_rows = []

    for row in jobs.itertuples(
        index=False
    ):
        role_family = (
            str(row.role_family)
            if pd.notna(
                row.role_family
            )
            else "Other Analyst"
        )

        company_name = (
            str(row.company_name).strip()
            if (
                pd.notna(
                    row.company_name
                )
                and str(
                    row.company_name
                ).strip()
            )
            else "Unknown Company"
        )

        city = (
            str(row.city)
            if pd.notna(
                row.city
            )
            else "Unknown"
        )

        state = (
            str(row.state)
            if pd.notna(
                row.state
            )
            else "Unknown"
        )

        location_name = (
            str(row.location_name)
            if pd.notna(
                row.location_name
            )
            else "Unknown"
        )

        location_scope = (
            str(row.location_scope)
            if pd.notna(
                row.location_scope
            )
            else "Unknown"
        )

        role_key = role_map[
            (
                role_family,
            )
        ]

        company_key = company_map[
            (
                company_name,
            )
        ]

        location_key = location_map[
            (
                city,
                state,
                location_name,
                location_scope,
            )
        ]

        fact_rows.append(
            (
                str(row.job_id),
                role_key,
                company_key,
                location_key,
                pd.to_datetime(
                    row.posted_date
                ).date(),
                to_none(
                    row.source
                ),
                to_none(
                    row.source_family
                ),
                to_none(
                    row.source_provider
                ),
                str(
                    row.title
                ),
                to_none(
                    row.description
                ),
                (
                    str(
                        row.work_mode
                    )
                    if pd.notna(
                        row.work_mode
                    )
                    else "Not Specified"
                ),
                to_none(
                    row.experience_min_years
                ),
                to_none(
                    row.experience_max_years
                ),
                (
                    str(
                        row.experience_band
                    )
                    if pd.notna(
                        row.experience_band
                    )
                    else "Not Specified"
                ),
                to_none(
                    row.salary_min_source
                ),
                to_none(
                    row.salary_max_source
                ),
                to_none(
                    row.salary_min
                ),
                to_none(
                    row.salary_max
                ),
                to_none(
                    row.salary_midpoint
                ),
                to_optional_bool(
                    row.salary_is_predicted
                ),
                to_bool(
                    row.has_salary_source
                ),
                to_bool(
                    row.salary_analysis_eligible
                ),
                to_none(
                    row.salary_normalization_status
                ),
                to_none(
                    row.salary_text_evidence
                ),
                int(
                    row.skill_count
                ),
                to_bool(
                    row.has_extracted_skill
                ),
                to_bool(
                    row.is_recent_90d
                ),
                to_bool(
                    row.is_complete_week
                ),
                to_none(
                    row.contract_type
                ),
                to_none(
                    row.contract_time
                ),
                to_none(
                    row.redirect_url
                ),
            )
        )

    execute_values(
        cur,
        """
        INSERT INTO job_market.fact_jobs (
            job_id,
            role_key,
            company_key,
            location_key,
            date_key,
            source,
            source_family,
            source_provider,
            title,
            description,
            work_mode,
            experience_min_years,
            experience_max_years,
            experience_band,
            salary_min_source,
            salary_max_source,
            salary_min,
            salary_max,
            salary_midpoint,
            salary_is_predicted,
            has_salary_source,
            salary_analysis_eligible,
            salary_normalization_status,
            salary_text_evidence,
            skill_count,
            has_extracted_skill,
            is_recent_90d,
            is_complete_week,
            contract_type,
            contract_time,
            redirect_url
        )
        VALUES %s
        """,
        fact_rows,
        page_size=1000,
    )


def load_bridge(
    cur,
    skills: pd.DataFrame,
) -> None:
    cur.execute(
        """
        SELECT
            job_id,
            job_key
        FROM job_market.fact_jobs
        """
    )

    job_map = {
        str(job_id): job_key
        for (
            job_id,
            job_key,
        )
        in cur.fetchall()
    }

    cur.execute(
        """
        SELECT
            skill,
            skill_key
        FROM job_market.dim_skill
        """
    )

    skill_map = {
        str(skill): skill_key
        for (
            skill,
            skill_key,
        )
        in cur.fetchall()
    }

    rows = []

    for row in skills.itertuples(
        index=False
    ):
        job_id = str(
            row.job_id
        )

        skill = str(
            row.skill
        )

        if job_id not in job_map:
            raise RuntimeError(
                f"Job identifier {job_id} "
                "is not present in fact_jobs."
            )

        if skill not in skill_map:
            raise RuntimeError(
                f"Skill {skill} "
                "is not present in dim_skill."
            )

        rows.append(
            (
                job_map[
                    job_id
                ],
                skill_map[
                    skill
                ],
            )
        )

    execute_values(
        cur,
        """
        INSERT INTO job_market.bridge_job_skill (
            job_key,
            skill_key
        )
        VALUES %s
        ON CONFLICT (
            job_key,
            skill_key
        ) DO NOTHING
        """,
        rows,
        page_size=1000,
    )


def scalar_count(
    cur,
    query: str,
) -> int:
    cur.execute(
        query
    )

    return int(
        cur.fetchone()[0]
    )


def validate_load(
    cur,
) -> None:
    fact_rows = scalar_count(
        cur,
        """
        SELECT COUNT(*)
        FROM job_market.fact_jobs
        """,
    )

    bridge_rows = scalar_count(
        cur,
        """
        SELECT COUNT(*)
        FROM job_market.bridge_job_skill
        """,
    )

    skill_rows = scalar_count(
        cur,
        """
        SELECT COUNT(*)
        FROM job_market.dim_skill
        """,
    )

    salary_rows = scalar_count(
        cur,
        """
        SELECT COUNT(*)
        FROM job_market.fact_jobs
        WHERE salary_analysis_eligible
        """,
    )

    duplicate_jobs = scalar_count(
        cur,
        """
        SELECT COUNT(*)
        FROM (
            SELECT job_id
            FROM job_market.fact_jobs
            GROUP BY job_id
            HAVING COUNT(*) > 1
        ) AS repeated_jobs
        """,
    )

    invalid_salary_rows = scalar_count(
        cur,
        """
        SELECT COUNT(*)
        FROM job_market.fact_jobs
        WHERE salary_analysis_eligible
          AND (
              salary_min IS NULL
              OR salary_max IS NULL
              OR salary_midpoint IS NULL
              OR salary_min <= 0
              OR salary_max <= 0
              OR salary_max < salary_min
          )
        """,
    )

    if fact_rows != EXPECTED_JOB_ROWS:
        raise RuntimeError(
            f"fact_jobs expected {EXPECTED_JOB_ROWS:,} rows "
            f"but contains {fact_rows:,}."
        )

    if bridge_rows != EXPECTED_SKILL_ROWS:
        raise RuntimeError(
            f"bridge_job_skill expected {EXPECTED_SKILL_ROWS:,} rows "
            f"but contains {bridge_rows:,}."
        )

    if skill_rows != EXPECTED_SKILLS:
        raise RuntimeError(
            f"dim_skill expected {EXPECTED_SKILLS:,} rows "
            f"but contains {skill_rows:,}."
        )

    if salary_rows != EXPECTED_SALARY_ROWS:
        raise RuntimeError(
            f"Expected {EXPECTED_SALARY_ROWS:,} salary-analysis rows "
            f"but contains {salary_rows:,}."
        )

    if duplicate_jobs != 0:
        raise RuntimeError(
            "fact_jobs contains repeated job_id values."
        )

    if invalid_salary_rows != 0:
        raise RuntimeError(
            "Salary-analysis rows failed database validation."
        )

    print(
        "=" * 78
    )
    print(
        "POSTGRESQL LOAD COMPLETE"
    )
    print(
        "=" * 78
    )
    print(
        f"Fact jobs:                  {fact_rows:,}"
    )
    print(
        f"Bridge job-skill rows:      {bridge_rows:,}"
    )
    print(
        f"Unique skills:              {skill_rows:,}"
    )
    print(
        f"Salary analysis rows:       {salary_rows:,}"
    )


def main() -> None:
    if not JOBS_FILE.exists():
        raise FileNotFoundError(
            f"Jobs file not found: {JOBS_FILE}"
        )

    if not SKILLS_FILE.exists():
        raise FileNotFoundError(
            f"Skill bridge file not found: {SKILLS_FILE}"
        )

    if not SCHEMA_FILE.exists():
        raise FileNotFoundError(
            f"Schema file not found: {SCHEMA_FILE}"
        )

    jobs = pd.read_csv(
        JOBS_FILE,
        low_memory=False,
    )

    skills = pd.read_csv(
        SKILLS_FILE,
        low_memory=False,
    )

    validate_inputs(
        jobs,
        skills,
    )

    connection = get_connection()

    try:
        with connection:
            with connection.cursor() as cur:
                run_schema(
                    cur
                )

                load_dimensions(
                    cur,
                    jobs,
                    skills,
                )

                load_fact_jobs(
                    cur,
                    jobs,
                )

                load_bridge(
                    cur,
                    skills,
                )

                validate_load(
                    cur
                )

    finally:
        connection.close()


if __name__ == "__main__":
    main()

    