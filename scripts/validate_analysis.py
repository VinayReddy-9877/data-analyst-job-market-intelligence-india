"""
Data Analyst Job Market Intelligence: Skill, Experience & Salary Analytics — India

Analytical validation checks.

Inputs
------
data/processed/job_postings_clean.csv
data/processed/job_skills_bridge.csv

Output
------
reports/validation_report.txt
"""

from __future__ import annotations

from pathlib import Path
import re
import unicodedata

import numpy as np
import pandas as pd


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

REPORT_FILE = (
    PROJECT_ROOT
    / "reports"
    / "validation_report.txt"
)

EXPECTED_JOBS = 4_035
EXPECTED_SKILL_ROWS = 6_213
EXPECTED_SKILLS = 44
WINDOW_START = pd.Timestamp("2026-01-01")
WINDOW_END = pd.Timestamp("2026-08-16")
RECENT_90D_START = pd.Timestamp("2026-05-19")


def as_boolean(series: pd.Series) -> pd.Series:
    if pd.api.types.is_bool_dtype(series):
        return series.fillna(False)

    normalized = (
        series.astype("string")
        .str.strip()
        .str.lower()
    )

    true_values = {
        "1",
        "1.0",
        "true",
        "yes",
        "y",
    }

    false_values = {
        "0",
        "0.0",
        "false",
        "no",
        "n",
        "<na>",
        "",
    }

    unexpected = (
        set(
            normalized.dropna().unique()
        )
        - true_values
        - false_values
    )

    if unexpected:
        raise RuntimeError(
            "Unexpected boolean values: "
            + ", ".join(
                sorted(unexpected)
            )
        )

    return normalized.isin(
        true_values
    )


def require(
    condition: bool,
    message: str,
) -> None:
    if not condition:
        raise RuntimeError(message)


def company_key(value: object) -> str:
    text = str(value).strip()
    ascii_text = (
        unicodedata.normalize(
            "NFKD",
            text,
        )
        .encode(
            "ascii",
            "ignore",
        )
        .decode("ascii")
    )
    return re.sub(
        r"[^a-z0-9]+",
        "",
        ascii_text.lower(),
    )


def main() -> None:
    if not JOBS_FILE.exists():
        raise FileNotFoundError(
            JOBS_FILE
        )

    if not SKILLS_FILE.exists():
        raise FileNotFoundError(
            SKILLS_FILE
        )

    jobs = pd.read_csv(
        JOBS_FILE,
        low_memory=False,
    )

    skills = pd.read_csv(
        SKILLS_FILE,
        low_memory=False,
    )

    required_job_columns = {
        "job_id",
        "posted_date",
        "week_start",
        "role_family",
        "company_name",
        "city",
        "location_scope",
        "experience_min_years",
        "experience_band",
        "has_extracted_skill",
        "has_salary_source",
        "salary_analysis_eligible",
        "salary_is_predicted",
        "salary_min",
        "salary_max",
        "salary_midpoint",
        "is_recent_90d",
        "is_complete_week",
    }

    missing_job_columns = sorted(
        required_job_columns
        - set(jobs.columns)
    )

    require(
        not missing_job_columns,
        "Processed dataset is missing required columns: "
        + ", ".join(missing_job_columns),
    )

    required_skill_columns = {
        "job_id",
        "skill",
    }

    missing_skill_columns = sorted(
        required_skill_columns
        - set(skills.columns)
    )

    require(
        not missing_skill_columns,
        "Skill bridge is missing required columns: "
        + ", ".join(missing_skill_columns),
    )

    test_company_names = {
        "testhiring",
        "test",
        "demo",
        "sample company",
        "xyz company",
        "abc company",
        "dummy",
    }

    company_names_normalized = (
        jobs["company_name"]
        .astype("string")
        .str.strip()
        .str.lower()
        .fillna("")
    )

    require(
        not company_names_normalized
        .isin(test_company_names)
        .any(),
        "Placeholder-company check failed.",
    )

    
    for column in [
        "has_extracted_skill",
        "has_salary_source",
        "salary_analysis_eligible",
        "is_recent_90d",
        "is_complete_week",
    ]:
        jobs[column] = as_boolean(
            jobs[column]
        )

    jobs["posted_date"] = pd.to_datetime(
        jobs["posted_date"],
        errors="raise",
    )

    jobs["week_start"] = pd.to_datetime(
        jobs["week_start"],
        errors="raise",
    )

    require(
        len(jobs) == EXPECTED_JOBS,
        "Vacancy row-count check failed.",
    )

    require(
        jobs["job_id"].nunique()
        == EXPECTED_JOBS,
        "Vacancy identifier check failed.",
    )

    require(
        not jobs["job_id"].duplicated().any(),
        "Vacancy identifier check failed.",
    )

    require(
        len(skills) == EXPECTED_SKILL_ROWS,
        "Job-skill row-count check failed.",
    )

    require(
        skills["skill"].nunique()
        == EXPECTED_SKILLS,
        "Skill-count check failed.",
    )

    require(
        not skills.duplicated(
            ["job_id", "skill"]
        ).any(),
        "Job-skill uniqueness check failed.",
    )

    require(
        set(
            skills["job_id"].astype(str)
        ).issubset(
            set(
                jobs["job_id"].astype(str)
            )
        ),
        "Job-skill key check failed.",
    )

    require(
        jobs["posted_date"].min()
        >= WINDOW_START,
        "Posting-date window check failed.",
    )

    require(
        jobs["posted_date"].max()
        <= WINDOW_END,
        "Posting-date window check failed.",
    )

    missing_experience = (
        jobs["experience_min_years"]
        .isna()
    )

    require(
        jobs.loc[
            missing_experience,
            "experience_band",
        ]
        .eq("Not Specified")
        .all(),
        "Experience-band check failed.",
    )

    require(
        jobs.loc[
            jobs["experience_band"].eq(
                "15+"
            ),
            "experience_min_years",
        ]
        .dropna()
        .ge(15)
        .all(),
        "Experience-band check failed.",
    )

    require(
        not jobs["city"].eq(
            "India"
        ).any(),
        "City-label check failed.",
    )

    require(
        jobs.loc[
            jobs["city"].eq(
                "City Not Specified"
            ),
            "location_scope",
        ]
        .eq(
            "India - City Not Specified"
        )
        .all(),
        "Location-scope check failed.",
    )

    company_labels = (
        jobs.loc[
            jobs["company_name"].ne(
                "Unknown Company"
            ),
            "company_name",
        ]
        .astype(str)
        .str.strip()
        .drop_duplicates()
    )

    company_keys = (
        company_labels
        .map(company_key)
    )

    require(
        not company_keys.duplicated(
            keep=False
        ).any(),
        "Employer-label standardization check failed.",
    )

    eligible = jobs[
        "salary_analysis_eligible"
    ]

    salary_predicted = as_boolean(
        jobs["salary_is_predicted"]
    )

    require(
        not salary_predicted.loc[eligible].any(),
        "Salary source check failed.",
    )

    salary_fields = jobs.loc[
        eligible,
        [
            "salary_min",
            "salary_max",
            "salary_midpoint",
        ],
    ].apply(
        pd.to_numeric,
        errors="coerce",
    )

    require(
        salary_fields.notna()
        .all()
        .all(),
        "Salary eligibility check failed.",
    )

    require(
        salary_fields[
            "salary_min"
        ].gt(0).all()
        and salary_fields[
            "salary_max"
        ].gt(0).all(),
        "Salary eligibility check failed.",
    )

    require(
        salary_fields[
            "salary_max"
        ]
        .ge(
            salary_fields[
                "salary_min"
            ]
        )
        .all(),
        "Salary eligibility check failed.",
    )

    expected_midpoint = (
        salary_fields[
            "salary_min"
        ]
        + salary_fields[
            "salary_max"
        ]
    ) / 2

    require(
        np.allclose(
            salary_fields[
                "salary_midpoint"
            ],
            expected_midpoint,
            rtol=0,
            atol=0.01,
        ),
        "Salary midpoint check failed.",
    )

    expected_recent = (
        jobs["posted_date"]
        .ge(RECENT_90D_START)
        & jobs["posted_date"]
        .le(WINDOW_END)
    )

    require(
        jobs["is_recent_90d"]
        .eq(expected_recent)
        .all(),
        "Recent-window check failed.",
    )

    dataset_min_date = jobs["posted_date"].min()
    dataset_max_date = jobs["posted_date"].max()

    first_complete_week = (
        dataset_min_date
        + pd.Timedelta(
            days=(
                7
                - dataset_min_date.weekday()
            ) % 7
        )
    ).normalize()

    expected_complete = (
        jobs["week_start"]
        .ge(first_complete_week)
        & (
            jobs["week_start"]
            + pd.Timedelta(days=6)
        ).le(dataset_max_date)
    )

    require(
        jobs["is_complete_week"]
        .eq(expected_complete)
        .all(),
        "Complete-week check failed.",
    )

    complete = jobs.loc[
        jobs["is_complete_week"]
    ]

    require(
        complete["week_start"]
        .dt.weekday
        .eq(0)
        .all(),
        "Complete-week check failed.",
    )

    role_total = (
        jobs.groupby(
            "role_family",
            dropna=False,
        )["job_id"]
        .nunique()
        .sum()
    )

    require(
        role_total
        == EXPECTED_JOBS,
        "Role-demand aggregation check failed.",
    )

    summary = [
        "DATA ANALYST JOB MARKET INTELLIGENCE",
        "ANALYTICAL VALIDATION",
        "=" * 72,
        "",
        f"unique_vacancies: {len(jobs):,}",
        f"job_skill_rows: {len(skills):,}",
        f"unique_skills: {skills['skill'].nunique():,}",
        f"experience_labeled: {int(jobs['experience_min_years'].notna().sum()):,}",
        f"experience_not_specified: {int(jobs['experience_band'].eq('Not Specified').sum()):,}",
        f"specific_city_vacancies: {int(jobs['location_scope'].eq('Specific City').sum()):,}",
        f"city_not_specified: {int(jobs['city'].eq('City Not Specified').sum()):,}",
        f"known_employer_vacancies: {int(jobs['company_name'].ne('Unknown Company').sum()):,}",
        f"unique_known_employers: {jobs.loc[jobs['company_name'].ne('Unknown Company'), 'company_name'].nunique():,}",
        f"salary_analysis_eligible: {int(eligible.sum()):,}",
        f"recent_90d_start_date: {RECENT_90D_START.date()}",
        f"recent_90d_vacancies: {int(jobs['is_recent_90d'].sum()):,}",
        f"complete_week_vacancies: {int(jobs['is_complete_week'].sum()):,}",
        "",
        "status: PASS",
    ]

    REPORT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    REPORT_FILE.write_text(
        "\n".join(summary) + "\n",
        encoding="utf-8",
    )

    print("=" * 78)
    print("ANALYTICAL VALIDATION PASS")
    print("=" * 78)
    print(
        f"Unique vacancies:          {len(jobs):,}"
    )
    print(
        f"Job-skill rows:            {len(skills):,}"
    )
    print(
        f"Unique skills:             {skills['skill'].nunique():,}"
    )
    print(
        f"Experience Not Specified: {int(jobs['experience_band'].eq('Not Specified').sum()):,}"
    )
    print(
        f"City Not Specified:       {int(jobs['city'].eq('City Not Specified').sum()):,}"
    )
    print(
        f"Recent 90-day start:      {RECENT_90D_START.date()}"
    )
    print(
        f"Salary analysis rows:     {int(eligible.sum()):,}"
    )
    print(
        f"Report:                   {REPORT_FILE}"
    )


if __name__ == "__main__":
    main()
