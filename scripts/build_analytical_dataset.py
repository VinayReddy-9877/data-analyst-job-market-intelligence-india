"""
Data Analyst Job Market Intelligence: Skill, Experience & Salary Analytics — India

Analytical dataset builder.

Input
-----
data/raw/job_postings_final_unique_4046.csv

Outputs
-------
data/processed/job_postings_clean.csv
data/processed/job_skills_bridge.csv
reports/analytical_dataset_report.txt
reports/role_scope_audit.csv
reports/skill_coverage_report.csv
"""

from __future__ import annotations

import json
import math
import re
import unicodedata
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

RAW_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "job_postings_final_unique_4046.csv"
)

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
REPORT_DIR = PROJECT_ROOT / "reports"

CLEAN_FILE = PROCESSED_DIR / "job_postings_clean.csv"
SKILL_BRIDGE_FILE = PROCESSED_DIR / "job_skills_bridge.csv"

REPORT_FILE = REPORT_DIR / "analytical_dataset_report.txt"
ROLE_AUDIT_FILE = REPORT_DIR / "role_scope_audit.csv"
SKILL_COVERAGE_FILE = REPORT_DIR / "skill_coverage_report.csv"

EXPECTED_INPUT_ROWS = 4_046

NON_PRODUCTION_COMPANY_NAMES = {
    "testhiring",
    "test",
    "demo",
    "sample company",
    "xyz company",
    "abc company",
    "dummy",
}

WINDOW_START = pd.Timestamp("2026-01-01T00:00:00Z")
WINDOW_END = pd.Timestamp("2026-08-16T23:59:59Z")


ROLE_RULES = [
    (
        "Data Analyst",
        [
            r"\bdata analyst\b",
            r"\bdata analytics analyst\b",
            r"\bdata analysis analyst\b",
        ],
    ),
    (
        "Business Analyst",
        [
            r"\bbusiness data analyst\b",
            r"\bbusiness analyst\b",
        ],
    ),
    (
        "BI Analyst",
        [
            r"\bbusiness intelligence analyst\b",
            r"\bbi analyst\b",
            r"\bbusiness intelligence\b",
        ],
    ),
    (
        "Reporting / MIS Analyst",
        [
            r"\breporting analyst\b",
            r"\bmis analyst\b",
            r"\bdata visualization analyst\b",
        ],
    ),
    (
        "Product Analyst",
        [
            r"\bproduct analytics analyst\b",
            r"\bproduct analyst\b",
            r"\bproduct analytics\b",
        ],
    ),
    (
        "Insights / Customer Analytics",
        [
            r"\bcustomer insights analyst\b",
            r"\binsights analyst\b",
            r"\bcustomer analytics analyst\b",
            r"\bcustomer analytics\b",
        ],
    ),
    (
        "Marketing Analytics",
        [
            r"\bmarketing analytics analyst\b",
            r"\bmarketing analyst\b",
            r"\bmarketing analytics\b",
        ],
    ),
    (
        "Data Quality / Governance",
        [
            r"\bdata quality analyst\b",
            r"\bdata governance analyst\b",
            r"\bdata management analyst\b",
            r"\bdata integrity analyst\b",
            r"\bdata validation analyst\b",
            r"\bdata quality\b",
            r"\bdata governance\b",
        ],
    ),
    (
        "Operations / Process Analytics",
        [
            r"\boperations analytics analyst\b",
            r"\boperations analyst\b",
            r"\bprocess analytics analyst\b",
            r"\boperations analytics\b",
            r"\bprocess analytics\b",
        ],
    ),
    (
        "Risk / Quantitative Analytics",
        [
            r"\brisk analytics analyst\b",
            r"\brisk analyst\b",
            r"\bquantitative analyst\b",
            r"\brisk analytics\b",
        ],
    ),
    (
        "Pricing / Revenue / Commercial",
        [
            r"\bpricing analyst\b",
            r"\brevenue analyst\b",
            r"\bcommercial analytics analyst\b",
            r"\bcommercial analyst\b",
            r"\bcommercial analytics\b",
        ],
    ),
    (
        "Performance / Strategy",
        [
            r"\bperformance analyst\b",
            r"\bstrategy analyst\b",
        ],
    ),
    (
        "Analytics Analyst",
        [
            r"\banalytics analyst\b",
            r"\banalytics associate\b",
        ],
    ),
]


CITY_ALIASES = {
    "bangalore": "Bengaluru",
    "bengaluru": "Bengaluru",
    "hyderabad": "Hyderabad",
    "pune": "Pune",
    "mumbai": "Mumbai",
    "navi mumbai": "Navi Mumbai",
    "thane": "Thane",
    "chennai": "Chennai",
    "gurgaon": "Gurugram",
    "gurugram": "Gurugram",
    "noida": "Noida",
    "new delhi": "Delhi",
    "delhi": "Delhi",
    "kolkata": "Kolkata",
    "calcutta": "Kolkata",
    "ahmedabad": "Ahmedabad",
    "kochi": "Kochi",
    "cochin": "Kochi",
    "jaipur": "Jaipur",
    "chandigarh": "Chandigarh",
    "coimbatore": "Coimbatore",
    "indore": "Indore",
    "vadodara": "Vadodara",
    "baroda": "Vadodara",
    "bhubaneswar": "Bhubaneswar",
    "visakhapatnam": "Visakhapatnam",
    "vizag": "Visakhapatnam",
    "lucknow": "Lucknow",
    "thiruvananthapuram": "Thiruvananthapuram",
    "trivandrum": "Thiruvananthapuram",
}


STATE_BY_CITY = {
    "Bengaluru": "Karnataka",
    "Hyderabad": "Telangana",
    "Pune": "Maharashtra",
    "Mumbai": "Maharashtra",
    "Navi Mumbai": "Maharashtra",
    "Thane": "Maharashtra",
    "Chennai": "Tamil Nadu",
    "Gurugram": "Haryana",
    "Noida": "Uttar Pradesh",
    "Delhi": "Delhi",
    "Kolkata": "West Bengal",
    "Ahmedabad": "Gujarat",
    "Kochi": "Kerala",
    "Jaipur": "Rajasthan",
    "Chandigarh": "Chandigarh",
    "Coimbatore": "Tamil Nadu",
    "Indore": "Madhya Pradesh",
    "Vadodara": "Gujarat",
    "Bhubaneswar": "Odisha",
    "Visakhapatnam": "Andhra Pradesh",
    "Lucknow": "Uttar Pradesh",
    "Thiruvananthapuram": "Kerala",
}


SKILL_RULES = {
    "SQL": [r"\bsql\b"],
    "Python": [r"\bpython\b"],
    "Excel": [
        r"\bmicrosoft excel\b",
        r"\bms excel\b",
        r"\bexcel\b",
    ],
    "Power BI": [
        r"\bpower\s*bi\b",
        r"\bpowerbi\b",
    ],
    "Tableau": [r"\btableau\b"],
    "R": [
        r"(?<![a-z0-9])r programming(?![a-z0-9])",
        r"(?<![a-z0-9])r language(?![a-z0-9])",
    ],
    "DAX": [r"\bdax\b"],
    "Power Query": [r"\bpower query\b"],
    "PostgreSQL": [
        r"\bpostgresql\b",
        r"\bpostgres\b",
    ],
    "MySQL": [r"\bmysql\b"],
    "Oracle": [
        r"\boracle sql\b",
        r"\boracle database\b",
        r"\boracle db\b",
    ],
    "SQL Server": [
        r"\bsql server\b",
        r"\bmssql\b",
    ],
    "BigQuery": [
        r"\bbigquery\b",
        r"\bgoogle big query\b",
    ],
    "Snowflake": [r"\bsnowflake\b"],
    "Redshift": [r"\bredshift\b"],
    "Databricks": [r"\bdatabricks\b"],
    "Azure": [
        r"\bmicrosoft azure\b",
        r"\bazure\b",
    ],
    "AWS": [
        r"\bamazon web services\b",
        r"\baws\b",
    ],
    "GCP": [
        r"\bgoogle cloud platform\b",
        r"\bgcp\b",
    ],
    "Looker": [r"\blooker\b"],
    "Qlik": [
        r"\bqlik sense\b",
        r"\bqlikview\b",
        r"\bqlik\b",
    ],
    "Alteryx": [r"\balteryx\b"],
    "dbt": [r"\bdbt\b"],
    "Airflow": [
        r"\bapache airflow\b",
        r"\bairflow\b",
    ],
    "Spark": [
        r"\bapache spark\b",
        r"\bpyspark\b",
        r"\bspark\b",
    ],
    "Hadoop": [r"\bhadoop\b"],
    "ETL": [r"\betl\b"],
    "ELT": [r"\belt\b"],
    "Data Modeling": [
        r"\bdata modelling\b",
        r"\bdata modeling\b",
        r"\bdimensional modeling\b",
        r"\bdimensional modelling\b",
    ],
    "Data Warehousing": [
        r"\bdata warehouse\b",
        r"\bdata warehousing\b",
    ],
    "Statistics": [
        r"\bstatistics\b",
        r"\bstatistical analysis\b",
        r"\bstatistical modelling\b",
        r"\bstatistical modeling\b",
    ],
    "A/B Testing": [
        r"\ba/?b testing\b",
        r"\bab testing\b",
        r"\bexperimentation\b",
    ],
    "Regression": [r"\bregression\b"],
    "Forecasting": [r"\bforecasting\b"],
    "Machine Learning": [
        r"\bmachine learning\b",
        r"\bml models?\b",
    ],
    "Pandas": [r"\bpandas\b"],
    "NumPy": [r"\bnumpy\b"],
    "SciPy": [r"\bscipy\b"],
    "Git": [
        r"\bgit\b",
        r"\bgithub\b",
        r"\bgitlab\b",
    ],
    "Jira": [r"\bjira\b"],
    "SSIS": [r"\bssis\b"],
    "SAP": [r"\bsap\b"],
    "SAS": [r"\bsas\b"],
    "SPSS": [r"\bspss\b"],
}


SKILL_CATEGORIES = {
    "SQL": "Database / Query",
    "Python": "Programming",
    "Excel": "Spreadsheet",
    "Power BI": "BI / Visualization",
    "Tableau": "BI / Visualization",
    "R": "Programming",
    "DAX": "BI / Visualization",
    "Power Query": "BI / Visualization",
    "PostgreSQL": "Database / Query",
    "MySQL": "Database / Query",
    "Oracle": "Database / Query",
    "SQL Server": "Database / Query",
    "BigQuery": "Cloud / Warehouse",
    "Snowflake": "Cloud / Warehouse",
    "Redshift": "Cloud / Warehouse",
    "Databricks": "Data Engineering",
    "Azure": "Cloud",
    "AWS": "Cloud",
    "GCP": "Cloud",
    "Looker": "BI / Visualization",
    "Qlik": "BI / Visualization",
    "Alteryx": "Analytics Tool",
    "dbt": "Data Engineering",
    "Airflow": "Data Engineering",
    "Spark": "Data Engineering",
    "Hadoop": "Data Engineering",
    "ETL": "Data Engineering",
    "ELT": "Data Engineering",
    "Data Modeling": "Data Engineering",
    "Data Warehousing": "Data Engineering",
    "Statistics": "Statistics / Analytics",
    "A/B Testing": "Statistics / Analytics",
    "Regression": "Statistics / Analytics",
    "Forecasting": "Statistics / Analytics",
    "Machine Learning": "Machine Learning",
    "Pandas": "Programming",
    "NumPy": "Programming",
    "SciPy": "Programming",
    "Git": "Developer Tool",
    "Jira": "Collaboration Tool",
    "SSIS": "Data Engineering",
    "SAP": "Enterprise Tool",
    "SAS": "Statistics / Analytics",
    "SPSS": "Statistics / Analytics",
}


EXPERIENCE_PATTERNS = [
    re.compile(
        r"\b(\d{1,2})\s*(?:-|–|to)\s*(\d{1,2})\s*(?:years?|yrs?)\b",
        flags=re.I,
    ),
    re.compile(
        r"\b(?:minimum|min\.?|at least)\s*(?:of\s*)?(\d{1,2})\+?\s*(?:years?|yrs?)\b",
        flags=re.I,
    ),
    re.compile(
        r"\b(\d{1,2})\+\s*(?:years?|yrs?)\b",
        flags=re.I,
    ),
    re.compile(
        r"\b(\d{1,2})\s*(?:years?|yrs?)\s+(?:of\s+)?experience\b",
        flags=re.I,
    ),
]


def clean_text(value: Any) -> str:
    if value is None:
        return ""

    try:
        if pd.isna(value):
            return ""
    except Exception:
        pass

    return re.sub(
        r"\s+",
        " ",
        str(value),
    ).strip()


def normalized_text(value: Any) -> str:
    text = clean_text(value).lower()
    text = text.replace("&", " and ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def company_key(value: Any) -> str:
    text = clean_text(value)
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


def canonicalize_company_names(
    series: pd.Series,
) -> pd.Series:
    cleaned = (
        series
        .map(clean_text)
        .replace(
            "",
            "Unknown Company",
        )
    )

    counts = cleaned.value_counts(
        dropna=False
    )

    groups: dict[
        str,
        list[tuple[str, int]],
    ] = {}

    for name, count in counts.items():
        key = company_key(name)
        groups.setdefault(
            key,
            [],
        ).append(
            (
                str(name),
                int(count),
            )
        )

    display_by_name: dict[
        str,
        str,
    ] = {}

    for variants in groups.values():
        readable = [
            item
            for item in variants
            if not (
                any(
                    ch.isalpha()
                    for ch in item[0]
                )
                and all(
                    not ch.isalpha()
                    or ch.islower()
                    for ch in item[0]
                )
            )
        ]

        pool = (
            readable
            if readable
            else variants
        )

        display_name = sorted(
            pool,
            key=lambda item: (
                -item[1],
                item[0],
            ),
        )[0][0]

        for name, _ in variants:
            display_by_name[
                name
            ] = display_name

    return cleaned.map(
        display_by_name
    )


def boolean_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value

    if value is None:
        return False

    try:
        if pd.isna(value):
            return False
    except Exception:
        pass

    if isinstance(value, (int, float, np.integer, np.floating)):
        return float(value) == 1.0

    return str(value).strip().lower() in {
        "1",
        "1.0",
        "true",
        "yes",
        "y",
    }


def source_family(value: Any) -> str:
    text = clean_text(value).lower()

    if "adzuna" in text:
        return "Adzuna"

    if text.startswith("freehire"):
        return "Freehire"

    return "Other"


def source_provider(value: Any) -> str:
    text = clean_text(value)

    if not text:
        return "Unknown"

    if "/" in text:
        provider = text.split("/", 1)[1].strip()
        return provider.title() if provider else "Unknown"

    if "adzuna" in text.lower():
        return "Adzuna"

    return text


def classify_role(title: Any) -> str:
    text = normalized_text(title)

    for family, patterns in ROLE_RULES:
        if any(
            re.search(
                pattern,
                text,
                flags=re.I,
            )
            for pattern in patterns
        ):
            return family

    return "Other Analyst"


def normalize_city(location: Any) -> str:
    text = normalized_text(location)

    if not text:
        return "Unknown"

    if "remote" in text and (
        "india" in text
        or text == "remote"
    ):
        return "Remote - India"

    country_tokens = [
        token
        for token in re.split(
            r"[^a-z]+",
            text,
        )
        if token
    ]

    if (
        country_tokens
        and set(
            country_tokens
        ) == {"india"}
    ):
        return "City Not Specified"

    for alias, canonical in CITY_ALIASES.items():
        if re.search(
            rf"\b{re.escape(alias)}\b",
            text,
            flags=re.I,
        ):
            return canonical

    first_piece = re.split(
        r"[,;|/]",
        clean_text(location),
        maxsplit=1,
    )[0].strip()

    if normalized_text(
        first_piece
    ) == "india":
        return "City Not Specified"

    return (
        first_piece
        if first_piece
        else "Unknown"
    )


def normalize_state(
    city: str,
    location: Any,
) -> str:
    if city in STATE_BY_CITY:
        return STATE_BY_CITY[city]

    if city == "City Not Specified":
        return "India"

    text = normalized_text(location)

    state_tokens = {
        "karnataka": "Karnataka",
        "telangana": "Telangana",
        "maharashtra": "Maharashtra",
        "tamil nadu": "Tamil Nadu",
        "haryana": "Haryana",
        "uttar pradesh": "Uttar Pradesh",
        "west bengal": "West Bengal",
        "gujarat": "Gujarat",
        "kerala": "Kerala",
        "rajasthan": "Rajasthan",
        "madhya pradesh": "Madhya Pradesh",
        "odisha": "Odisha",
        "andhra pradesh": "Andhra Pradesh",
        "punjab": "Punjab",
        "delhi": "Delhi",
    }

    for token, canonical in state_tokens.items():
        if token in text:
            return canonical

    if city == "Remote - India":
        return "Remote - India"

    return "Unknown"


def classify_work_mode(
    title: Any,
    description: Any,
    location: Any,
) -> str:
    text = " ".join(
        [
            normalized_text(title),
            normalized_text(description),
            normalized_text(location),
        ]
    )

    if re.search(
        r"\bhybrid\b",
        text,
        flags=re.I,
    ):
        return "Hybrid"

    if re.search(
        r"\b(remote|work from home|wfh|work remotely)\b",
        text,
        flags=re.I,
    ):
        return "Remote"

    if re.search(
        r"\b(on[- ]?site|onsite|in[- ]office|in office)\b",
        text,
        flags=re.I,
    ):
        return "On-site"

    return "Not Specified"


def extract_experience(
    title: Any,
    description: Any,
) -> tuple[float | None, float | None]:
    text = " ".join(
        [
            clean_text(title),
            clean_text(description),
        ]
    )

    values: list[
        tuple[float, float]
    ] = []

    for pattern in EXPERIENCE_PATTERNS:
        for match in pattern.finditer(text):
            groups = match.groups()

            try:
                low = float(groups[0])

                if (
                    len(groups) > 1
                    and groups[1] is not None
                ):
                    high = float(groups[1])
                else:
                    high = low

                if (
                    0 <= low <= 30
                    and 0 <= high <= 30
                    and high >= low
                ):
                    values.append(
                        (low, high)
                    )
            except Exception:
                continue

    if not values:
        return None, None

    values.sort(
        key=lambda item: (
            item[0],
            item[1],
        )
    )

    return values[0]


def experience_band(
    minimum: float | None,
) -> str:
    if minimum is None or pd.isna(minimum):
        return "Not Specified"

    value = float(minimum)

    bands = [
        (0, 1, "0–1"),
        (1, 2, "1–2"),
        (2, 3, "2–3"),
        (3, 4, "3–4"),
        (4, 5, "4–5"),
        (5, 6, "5–6"),
        (6, 7, "6–7"),
        (7, 8, "7–8"),
        (8, 9, "8–9"),
        (9, 10, "9–10"),
        (10, 15, "10–15"),
    ]

    for low, high, label in bands:
        if low <= value < high:
            return label

    return "15+"


def salary_flags(
    salary_min: Any,
    salary_max: Any,
    salary_predicted: Any,
) -> tuple[bool, bool]:
    minimum = pd.to_numeric(
        pd.Series([salary_min]),
        errors="coerce",
    ).iloc[0]

    maximum = pd.to_numeric(
        pd.Series([salary_max]),
        errors="coerce",
    ).iloc[0]

    predicted = boolean_value(
        salary_predicted
    )

    has_any = (
        pd.notna(minimum)
        or pd.notna(maximum)
    )

    has_both = (
        pd.notna(minimum)
        and pd.notna(maximum)
    )

    positive = (
        has_both
        and minimum > 0
        and maximum > 0
    )

    ordered = (
        has_both
        and maximum >= minimum
    )

    eligible = bool(
        has_both
        and positive
        and ordered
        and not predicted
    )

    return bool(has_any), eligible


SALARY_ANNUAL_SCALE_THRESHOLD = 300_000
SALARY_EVIDENCE_TOLERANCE = 0.35

MONTHLY_SALARY_PATTERNS = [
    re.compile(
        r"(?:salary|budget|ctc)[^.\n]{0,120}?"
        r"(?:₹|rs\.?|inr)?\s*([\d,]+(?:\.\d+)?)\s*"
        r"(?:per\s+month|monthly|/month|p\.?m\.?)\b",
        flags=re.IGNORECASE,
    ),
    re.compile(
        r"(?:₹|rs\.?|inr)\s*([\d,]+(?:\.\d+)?)\s*"
        r"(?:per\s+month|monthly|/month|p\.?m\.?)\b",
        flags=re.IGNORECASE,
    ),
]

LPA_SALARY_PATTERNS = [
    re.compile(
        r"(?:salary|budget|ctc)?[^.\n]{0,100}?"
        r"([\d]+(?:\.\d+)?)\s*"
        r"(?:lpa|lakhs?\s+per\s+annum)\b",
        flags=re.IGNORECASE,
    ),
]

ANNUAL_RUPEE_PATTERNS = [
    re.compile(
        r"(?:salary|budget|ctc)[^.\n]{0,120}?"
        r"(?:₹|rs\.?|inr)?\s*([\d,]+(?:\.\d+)?)\s*"
        r"(?:per\s+annum|per\s+year|yearly|annual(?:ly)?)\b",
        flags=re.IGNORECASE,
    ),
]


def parse_salary_number(
    value: Any,
) -> float:
    if value is None:
        return np.nan

    try:
        return float(
            str(value).replace(",", "")
        )
    except (TypeError, ValueError):
        return np.nan


def within_salary_tolerance(
    observed: Any,
    target: Any,
    tolerance: float = SALARY_EVIDENCE_TOLERANCE,
) -> bool:
    observed_value = pd.to_numeric(
        pd.Series([observed]),
        errors="coerce",
    ).iloc[0]

    target_value = pd.to_numeric(
        pd.Series([target]),
        errors="coerce",
    ).iloc[0]

    if (
        pd.isna(observed_value)
        or pd.isna(target_value)
        or target_value <= 0
    ):
        return False

    return (
        abs(
            observed_value
            - target_value
        )
        / target_value
        <= tolerance
    )


def salary_text_evidence(
    description: Any,
) -> tuple[str, float | None, str]:
    text = clean_text(
        description
    )

    if not text:
        return (
            "UNKNOWN",
            None,
            "No explicit salary-period evidence",
        )

    for pattern in MONTHLY_SALARY_PATTERNS:
        match = pattern.search(text)

        if match:
            amount = parse_salary_number(
                match.group(1)
            )

            if pd.notna(amount):
                return (
                    "MONTHLY",
                    float(amount),
                    match.group(0)[:180],
                )

    for pattern in LPA_SALARY_PATTERNS:
        match = pattern.search(text)

        if match:
            lpa = parse_salary_number(
                match.group(1)
            )

            if pd.notna(lpa):
                return (
                    "ANNUAL",
                    float(lpa) * 100_000,
                    match.group(0)[:180],
                )

    for pattern in ANNUAL_RUPEE_PATTERNS:
        match = pattern.search(text)

        if match:
            amount = parse_salary_number(
                match.group(1)
            )

            if pd.notna(amount):
                return (
                    "ANNUAL",
                    float(amount),
                    match.group(0)[:180],
                )

    return (
        "UNKNOWN",
        None,
        "No explicit salary-period evidence",
    )


def normalize_salary_for_analysis(
    salary_min: Any,
    salary_max: Any,
    salary_predicted: Any,
    description: Any,
) -> tuple[
    Any,
    Any,
    bool,
    bool,
    Any,
    str,
    str,
]:
    has_source, base_eligible = salary_flags(
        salary_min,
        salary_max,
        salary_predicted,
    )

    minimum = pd.to_numeric(
        pd.Series([salary_min]),
        errors="coerce",
    ).iloc[0]

    maximum = pd.to_numeric(
        pd.Series([salary_max]),
        errors="coerce",
    ).iloc[0]

    if not base_eligible:
        return (
            pd.NA,
            pd.NA,
            has_source,
            False,
            pd.NA,
            "Not Eligible",
            "No usable source salary range",
        )

    midpoint = (
        minimum + maximum
    ) / 2

    unit, stated_amount, evidence = (
        salary_text_evidence(
            description
        )
    )

    if (
        unit == "MONTHLY"
        and stated_amount is not None
    ):
        annual_target = (
            stated_amount * 12
        )

        if within_salary_tolerance(
            midpoint,
            annual_target,
        ):
            return (
                minimum,
                maximum,
                has_source,
                True,
                midpoint,
                "Monthly Evidence - Source Annualized",
                evidence,
            )

        if within_salary_tolerance(
            midpoint,
            stated_amount,
        ):
            annual_min = minimum * 12
            annual_max = maximum * 12

            return (
                annual_min,
                annual_max,
                has_source,
                True,
                (
                    annual_min
                    + annual_max
                ) / 2,
                "Annualized from Monthly",
                evidence,
            )

        return (
            pd.NA,
            pd.NA,
            has_source,
            False,
            pd.NA,
            "Ambiguous Salary Period",
            evidence,
        )

    if (
        unit == "ANNUAL"
        and stated_amount is not None
    ):
        if within_salary_tolerance(
            midpoint,
            stated_amount,
        ):
            return (
                minimum,
                maximum,
                has_source,
                True,
                midpoint,
                "Annual Evidence",
                evidence,
            )

        annualized_midpoint = (
            midpoint * 12
        )

        if within_salary_tolerance(
            annualized_midpoint,
            stated_amount,
        ):
            annual_min = minimum * 12
            annual_max = maximum * 12

            return (
                annual_min,
                annual_max,
                has_source,
                True,
                (
                    annual_min
                    + annual_max
                ) / 2,
                "Annualized using LPA Evidence",
                evidence,
            )

        return (
            pd.NA,
            pd.NA,
            has_source,
            False,
            pd.NA,
            "Ambiguous Salary Period",
            evidence,
        )

    if (
        midpoint
        >= SALARY_ANNUAL_SCALE_THRESHOLD
    ):
        return (
            minimum,
            maximum,
            has_source,
            True,
            midpoint,
            "Annual Scale",
            evidence,
        )

    return (
        pd.NA,
        pd.NA,
        has_source,
        False,
        pd.NA,
        "Ambiguous Salary Period",
        evidence,
    )


def extract_skills(
    title: Any,
    description: Any,
) -> list[str]:
    text = " ".join(
        [
            normalized_text(title),
            normalized_text(description),
        ]
    )

    skills = []

    for skill, patterns in SKILL_RULES.items():
        if any(
            re.search(
                pattern,
                text,
                flags=re.I,
            )
            for pattern in patterns
        ):
            skills.append(skill)

    return sorted(
        set(skills)
    )


def main() -> None:
    PROCESSED_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    REPORT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    if not RAW_FILE.exists():
        raise FileNotFoundError(
            f"Dataset not found: {RAW_FILE}"
        )

    df = pd.read_csv(
        RAW_FILE,
        low_memory=False,
    )

    if len(df) != EXPECTED_INPUT_ROWS:
        raise RuntimeError(
            f"Expected {EXPECTED_INPUT_ROWS:,} rows but found {len(df):,}."
        )

    if df["job_id"].astype(
        "string"
    ).duplicated().any():
        raise RuntimeError(
            "Repeated job_id values are present."
        )

    df["created_at"] = pd.to_datetime(
        df["created"],
        errors="coerce",
        utc=True,
    )

    outside = (
        df["created_at"].isna()
        | (df["created_at"] < WINDOW_START)
        | (df["created_at"] > WINDOW_END)
    )

    if outside.any():
        raise RuntimeError(
            "Rows outside the posting-date window are present."
        )

    raw_unique_vacancies = len(df)

    normalized_company_names = (
        df["company_name"]
        .astype("string")
        .str.strip()
        .str.lower()
        .fillna("")
    )

    non_production_mask = (
        normalized_company_names
        .isin(NON_PRODUCTION_COMPANY_NAMES)
    )

    non_production_postings_excluded = int(
        non_production_mask.sum()
    )

    df = df.loc[
        ~non_production_mask
    ].copy()

    print(
        f"Excluded non-production postings: "
        f"{non_production_postings_excluded:,}"
    )

    df["company_name"] = (
        canonicalize_company_names(
            df["company_name"]
        )
    )
    df["source_family"] = df[
        "source"
    ].map(source_family)

    df["source_provider"] = df[
        "source"
    ].map(source_provider)

    df["role_family"] = df[
        "title"
    ].map(classify_role)

    df["city"] = df[
        "location_name"
    ].map(normalize_city)

    df["state"] = [
        normalize_state(
            city,
            location,
        )
        for city, location
        in zip(
            df["city"],
            df["location_name"],
        )
    ]

    df["location_scope"] = np.where(
        df["city"].eq("Remote - India"),
        "Remote India",
        np.where(
            df["city"].eq("City Not Specified"),
            "India - City Not Specified",
            np.where(
                df["city"].eq("Unknown"),
                "Unknown",
                "Specific City",
            ),
        ),
    )

    df["work_mode"] = [
        classify_work_mode(
            title,
            description,
            location,
        )
        for title, description, location
        in zip(
            df["title"],
            df["description"],
            df["location_name"],
        )
    ]

    experience_pairs = [
        extract_experience(
            title,
            description,
        )
        for title, description
        in zip(
            df["title"],
            df["description"],
        )
    ]

    df["experience_min_years"] = [
        pair[0]
        for pair in experience_pairs
    ]

    df["experience_max_years"] = [
        pair[1]
        for pair in experience_pairs
    ]

    df["experience_band"] = df[
        "experience_min_years"
    ].map(experience_band)

    df["salary_min_source"] = pd.to_numeric(
        df.get(
            "salary_min",
            pd.Series(
                [pd.NA] * len(df)
            ),
        ),
        errors="coerce",
    )

    df["salary_max_source"] = pd.to_numeric(
        df.get(
            "salary_max",
            pd.Series(
                [pd.NA] * len(df)
            ),
        ),
        errors="coerce",
    )

    salary_results = [
        normalize_salary_for_analysis(
            salary_min,
            salary_max,
            salary_predicted,
            description,
        )
        for (
            salary_min,
            salary_max,
            salary_predicted,
            description,
        )
        in zip(
            df["salary_min_source"],
            df["salary_max_source"],
            df.get(
                "salary_is_predicted",
                pd.Series(
                    [pd.NA] * len(df)
                ),
            ),
            df.get(
                "description",
                pd.Series(
                    [""] * len(df)
                ),
            ),
        )
    ]

    df["salary_min"] = [
        item[0]
        for item in salary_results
    ]

    df["salary_max"] = [
        item[1]
        for item in salary_results
    ]

    df["has_salary_source"] = [
        item[2]
        for item in salary_results
    ]

    df["salary_analysis_eligible"] = [
        item[3]
        for item in salary_results
    ]

    df["salary_midpoint"] = [
        item[4]
        for item in salary_results
    ]

    df["salary_normalization_status"] = [
        item[5]
        for item in salary_results
    ]

    df["salary_text_evidence"] = [
        item[6]
        for item in salary_results
    ]

    df["posted_date"] = df[
        "created_at"
    ].dt.date

    df["posted_month"] = (
        df["created_at"]
        .dt.tz_convert(None)
        .dt.to_period(
            "M"
        )
        .astype(str)
    )

    df["week_start"] = (
        df["created_at"]
        - pd.to_timedelta(
            df["created_at"].dt.weekday,
            unit="D",
        )
    ).dt.date

    window_end_date = WINDOW_END.date()
    recent_start_date = (
        window_end_date
        - pd.Timedelta(
            days=89
        )
    )

    df["is_recent_90d"] = (
        pd.to_datetime(
            df["posted_date"]
        ).dt.date
        >= recent_start_date
    )

    dataset_min_date = min(
        df["posted_date"]
    )
    dataset_max_date = max(
        df["posted_date"]
    )

    first_complete_week = (
        pd.Timestamp(
            dataset_min_date
        )
        + pd.Timedelta(
            days=(
                7
                - pd.Timestamp(
                    dataset_min_date
                ).weekday()
            ) % 7
        )
    ).date()

    df["is_complete_week"] = (
        pd.to_datetime(
            df["week_start"]
        ).dt.date
        >= first_complete_week
    ) & (
        (
            pd.to_datetime(
                df["week_start"]
            )
            + pd.Timedelta(
                days=6
            )
        ).dt.date
        <= dataset_max_date
    )

    skills_per_job = [
        extract_skills(
            title,
            description,
        )
        for title, description
        in zip(
            df["title"],
            df["description"],
        )
    ]

    df["skill_count"] = [
        len(skills)
        for skills in skills_per_job
    ]

    df["has_extracted_skill"] = (
        df["skill_count"] > 0
    )

    bridge_rows = []

    for job_id, skills in zip(
        df["job_id"],
        skills_per_job,
    ):
        for skill in skills:
            bridge_rows.append(
                {
                    "job_id": job_id,
                    "skill": skill,
                    "skill_category": SKILL_CATEGORIES.get(
                        skill,
                        "Other",
                    ),
                }
            )

    bridge = pd.DataFrame(
        bridge_rows,
        columns=[
            "job_id",
            "skill",
            "skill_category",
        ],
    )

    if not bridge.empty:
        bridge = bridge.drop_duplicates(
            subset=[
                "job_id",
                "skill",
            ],
            keep="first",
        ).reset_index(
            drop=True
        )

    clean_columns = [
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
        "created_at",
        "posted_date",
        "posted_month",
        "week_start",
        "is_recent_90d",
        "is_complete_week",
        "experience_min_years",
        "experience_max_years",
        "experience_band",
        "salary_min_source",
        "salary_max_source",
        "salary_min",
        "salary_max",
        "salary_is_predicted",
        "has_salary_source",
        "salary_analysis_eligible",
        "salary_midpoint",
        "salary_normalization_status",
        "salary_text_evidence",
        "skill_count",
        "has_extracted_skill",
        "contract_type",
        "contract_time",
        "redirect_url",
    ]

    for column in clean_columns:
        if column not in df.columns:
            df[column] = pd.NA

    clean = df[
        clean_columns
    ].copy()

    missing_experience_rows = int(
        clean["experience_min_years"].isna().sum()
    )

    unspecified_band_rows = int(
        clean["experience_band"]
        .eq("Not Specified")
        .sum()
    )

    if missing_experience_rows != unspecified_band_rows:
        raise RuntimeError(
            "Experience band integrity check failed."
        )

    if (
        clean.loc[
            clean["experience_band"].eq("15+"),
            "experience_min_years",
        ]
        .dropna()
        .lt(15)
        .any()
    ):
        raise RuntimeError(
            "Experience band integrity check failed."
        )

    if clean["city"].eq(
        "India"
    ).any():
        raise RuntimeError(
            "City label integrity check failed."
        )

    if not (
        clean.loc[
            clean["city"].eq(
                "City Not Specified"
            ),
            "location_scope",
        ]
        .eq(
            "India - City Not Specified"
        )
        .all()
    ):
        raise RuntimeError(
            "Location scope integrity check failed."
        )

    eligible_salary = clean[
        "salary_analysis_eligible"
    ].astype(bool)

    if (
        clean.loc[
            eligible_salary,
            [
                "salary_min",
                "salary_max",
                "salary_midpoint",
            ],
        ]
        .isna()
        .any()
        .any()
    ):
        raise RuntimeError(
            "Salary eligibility integrity check failed."
        )

    if (
        pd.to_numeric(
            clean.loc[
                eligible_salary,
                "salary_min",
            ],
            errors="coerce",
        )
        .le(0)
        .any()
        or pd.to_numeric(
            clean.loc[
                eligible_salary,
                "salary_max",
            ],
            errors="coerce",
        )
        .le(0)
        .any()
    ):
        raise RuntimeError(
            "Salary eligibility integrity check failed."
        )

    if (
        pd.to_numeric(
            clean.loc[
                eligible_salary,
                "salary_max",
            ],
            errors="coerce",
        )
        < pd.to_numeric(
            clean.loc[
                eligible_salary,
                "salary_min",
            ],
            errors="coerce",
        )
    ).any():
        raise RuntimeError(
            "Salary eligibility integrity check failed."
        )

    recent_dates = pd.to_datetime(
        clean.loc[
            clean["is_recent_90d"].astype(bool),
            "posted_date",
        ],
        errors="raise",
    ).dt.date

    if len(recent_dates):
        if min(recent_dates) < recent_start_date:
            raise RuntimeError(
                "Recent-window integrity check failed."
            )

    non_recent_dates = pd.to_datetime(
        clean.loc[
            ~clean["is_recent_90d"].astype(bool),
            "posted_date",
        ],
        errors="raise",
    ).dt.date

    if len(non_recent_dates):
        if max(non_recent_dates) >= recent_start_date:
            raise RuntimeError(
                "Recent-window integrity check failed."
            )

    complete_week_rows = clean[
        "is_complete_week"
    ].astype(bool)

    complete_week_starts = pd.to_datetime(
        clean.loc[
            complete_week_rows,
            "week_start",
        ],
        errors="raise",
    )

    if len(complete_week_starts):
        if not (
            complete_week_starts.dt.weekday
            == 0
        ).all():
            raise RuntimeError(
                "Complete-week integrity check failed."
            )

    clean.to_csv(
        CLEAN_FILE,
        index=False,
        encoding="utf-8-sig",
    )

    bridge.to_csv(
        SKILL_BRIDGE_FILE,
        index=False,
        encoding="utf-8-sig",
    )

    role_audit = (
        clean["role_family"]
        .value_counts(
            dropna=False
        )
        .rename_axis(
            "role_family"
        )
        .reset_index(
            name="job_count"
        )
    )

    role_audit["share_pct"] = (
        role_audit["job_count"]
        / len(clean)
        * 100
    ).round(2)

    role_audit.to_csv(
        ROLE_AUDIT_FILE,
        index=False,
        encoding="utf-8-sig",
    )

    if bridge.empty:
        skill_coverage = pd.DataFrame(
            columns=[
                "skill",
                "skill_category",
                "job_count",
                "share_pct",
            ]
        )
    else:
        skill_coverage = (
            bridge.groupby(
                [
                    "skill",
                    "skill_category",
                ],
                as_index=False,
            )["job_id"]
            .nunique()
            .rename(
                columns={
                    "job_id": "job_count"
                }
            )
        )

        skill_coverage[
            "share_pct"
        ] = (
            skill_coverage["job_count"]
            / len(clean)
            * 100
        ).round(2)

        skill_coverage = (
            skill_coverage.sort_values(
                [
                    "job_count",
                    "skill",
                ],
                ascending=[
                    False,
                    True,
                ],
            )
            .reset_index(
                drop=True
            )
        )

    skill_coverage.to_csv(
        SKILL_COVERAGE_FILE,
        index=False,
        encoding="utf-8-sig",
    )

    other_share = (
        (
            clean["role_family"]
            == "Other Analyst"
        ).mean()
        * 100
    )

    skill_job_coverage = (
        clean[
            "has_extracted_skill"
        ].mean()
        * 100
    )

    experience_coverage = (
        clean[
            "experience_min_years"
        ].notna().mean()
        * 100
    )

    salary_source_coverage = (
        clean[
            "has_salary_source"
        ].mean()
        * 100
    )

    salary_eligible_coverage = (
        clean[
            "salary_analysis_eligible"
        ].mean()
        * 100
    )

    salary_status_counts = (
        clean[
            "salary_normalization_status"
        ]
        .fillna("Not Available")
        .value_counts(
            dropna=False
        )
    )

    salary_ambiguous_rows = int(
        salary_status_counts.get(
            "Ambiguous Salary Period",
            0,
        )
    )

    salary_annualized_rows = int(
        salary_status_counts.get(
            "Annualized from Monthly",
            0,
        )
        + salary_status_counts.get(
            "Annualized using LPA Evidence",
            0,
        )
    )

    report = [
        "DATA ANALYST JOB MARKET INTELLIGENCE",
        "ANALYTICAL DATASET REPORT",
        "=" * 78,
        "",
        f"raw_unique_vacancies: {raw_unique_vacancies:,}",
        f"non_production_postings_excluded: {non_production_postings_excluded:,}",
        f"processed_job_rows: {len(clean):,}",
        f"skill_bridge_rows: {len(bridge):,}",
        f"unique_skills: {bridge['skill'].nunique() if not bridge.empty else 0:,}",
        f"role_other_share_pct: {other_share:.2f}",
        f"skill_job_coverage_pct: {skill_job_coverage:.2f}",
        f"experience_extraction_coverage_pct: {experience_coverage:.2f}",
        f"experience_not_specified_rows: {int(clean['experience_band'].eq('Not Specified').sum()):,}",
        f"city_not_specified_rows: {int(clean['city'].eq('City Not Specified').sum()):,}",
        f"known_company_rows: {int(clean['company_name'].ne('Unknown Company').sum()):,}",
        f"salary_source_coverage_pct: {salary_source_coverage:.2f}",
        f"salary_analysis_eligible_coverage_pct: {salary_eligible_coverage:.2f}",
        f"salary_ambiguous_period_rows: {salary_ambiguous_rows:,}",
        f"salary_annualized_rows: {salary_annualized_rows:,}",
        f"recent_90d_start_date: {recent_start_date}",
        f"recent_90d_rows: {int(clean['is_recent_90d'].sum()):,}",
        f"complete_week_rows: {int(clean['is_complete_week'].sum()):,}",
        "",
        f"clean_file: {CLEAN_FILE.relative_to(PROJECT_ROOT).as_posix()}",
        f"skill_bridge_file: {SKILL_BRIDGE_FILE.relative_to(PROJECT_ROOT).as_posix()}",
        f"role_audit_file: {ROLE_AUDIT_FILE.relative_to(PROJECT_ROOT).as_posix()}",
        f"skill_coverage_file: {SKILL_COVERAGE_FILE.relative_to(PROJECT_ROOT).as_posix()}",
    ]

    REPORT_FILE.write_text(
        "\n".join(report) + "\n",
        encoding="utf-8",
    )

    print("=" * 78)
    print("ANALYTICAL DATASET CREATED")
    print("=" * 78)
    print(
        f"Processed jobs:               {len(clean):,}"
    )
    print(
        f"Skill bridge rows:            {len(bridge):,}"
    )
    print(
        f"Unique extracted skills:      {bridge['skill'].nunique() if not bridge.empty else 0:,}"
    )
    print(
        f"Other Analyst share:          {other_share:.2f}%"
    )
    print(
        f"Skill extraction coverage:    {skill_job_coverage:.2f}%"
    )
    print(
        f"Experience coverage:          {experience_coverage:.2f}%"
    )
    print(
        f"Experience Not Specified:     {int(clean['experience_band'].eq('Not Specified').sum()):,}"
    )
    print(
        f"City Not Specified:           {int(clean['city'].eq('City Not Specified').sum()):,}"
    )
    print(
        f"Recent 90-day start:          {recent_start_date}"
    )
    print(
        f"Complete-week rows:           {int(clean['is_complete_week'].sum()):,}"
    )
    print(
        f"Salary source coverage:       {salary_source_coverage:.2f}%"
    )
    print(
        f"Salary analysis coverage:     {salary_eligible_coverage:.2f}%"
    )
    print(
        f"Salary annualized rows:       {salary_annualized_rows:,}"
    )
    print(
        f"Salary ambiguous rows:        {salary_ambiguous_rows:,}"
    )
    print(
        f"Clean jobs:                   {CLEAN_FILE}"
    )
    print(
        f"Skill bridge:                 {SKILL_BRIDGE_FILE}"
    )
    print(
        f"Report:                       {REPORT_FILE}"
    )


if __name__ == "__main__":
    main()
