# Data Source and Analytical Scope

## Project Scope

This project analyzes real analytics-related job postings in India and converts the source snapshot into a validated analytical dataset for Python, PostgreSQL, SQL, statistics, and Power BI.

The reporting window is:

- **Analysis window:** 1 January 2026 to 16 August 2026
- **Observed posting dates:** 2 January 2026 to 16 August 2026
- **Recent 90-day comparison window:** 19 May 2026 to 16 August 2026
- **Weekly trend basis:** complete Monday-Sunday weeks only

## Source Snapshot

The raw source snapshot contains **4,046 unique vacancies**.

| Source family | Vacancies |
|---|---:|
| Adzuna | 2,400 |
| Freehire-backed employer feeds | 1,646 |
| **Total raw vacancies** | **4,046** |

Raw source file:

```text
data/raw/job_postings_final_unique_4046.csv
```

The source file preserves the original vacancy-level fields required for analysis, including `job_id`, job title, employer, location, description, salary fields, posting timestamp, and source/redirect information.

## Analytical Dataset

The analytical pipeline applies the project inclusion, standardization, extraction, and validation rules before reporting.

### Core analytical counts

| Analytical object | Count |
|---|---:|
| Processed analytical jobs | **4,035** |
| Unique analytical job IDs | **4,035** |
| Job-skill bridge rows | **6,213** |
| Unique normalized skills | **44** |
| Skill-tagged jobs | **1,744** |
| Salary-analysis eligible jobs | **110** |

Analytical inclusion rules retain **4,035 of the 4,046 source vacancies** for the final reporting dataset.

Processed files:

```text
data/processed/job_postings_clean.csv
data/processed/job_skills_bridge.csv
```

### Analytical grain

- `job_postings_clean.csv` — one row per validated analytical vacancy
- `job_skills_bridge.csv` — one unique vacancy-skill relationship per row

## Data Quality Rules

The pipeline applies the following rules before analysis:

- vacancy IDs must be unique,
- posting dates must fall within the project window,
- role titles must meet the analytical scope,
- equivalent employer labels are standardized,
- India-level locations are not treated as specific cities,
- missing experience remains `Not Specified`,
- skills are extracted only from explicit job-title or description evidence,
- duplicate vacancy-skill pairs are not retained,
- missing salary values remain missing,
- source-predicted salary is excluded from salary analysis,
- salary observations must satisfy the project eligibility rules,
- and weekly trend analysis uses complete weeks only.

The project does **not** create synthetic job rows or impute missing salary or experience values.

## Skill Scope

The processed skill bridge contains:

- **6,213** unique job-skill relationships
- **44** normalized skills
- **1,744** jobs with at least one extracted skill

The skill taxonomy covers commonly requested analyst tools and methods such as SQL, Excel, Power BI, Python, Tableau, statistics, data modeling, cloud platforms, ETL tools, machine learning, and related analytics technologies.

## Experience Scope

Experience is reported only when a usable requirement can be extracted from the posting.

- **Experience labeled:** 1,425 jobs
- **Experience not specified:** 2,610 jobs

`Not Specified` means that a usable experience requirement could not be extracted. It does not mean that the employer requires no prior experience.

## Salary Scope

Salary analysis uses only validated, analysis-eligible salary observations.

- **Salary-analysis eligible jobs:** 110
- **Salary coverage:** 2.73% of analytical jobs

Salary values are not imputed, and source-predicted salary is excluded from the analytical salary sample.

Because salary coverage is limited, salary findings are presented as exploratory and are always interpreted with sample-size context.

## Reporting Basis

The final analytical reporting layer is based on:

```text
4,035 analytical jobs
6,213 job-skill rows
44 normalized skills
110 salary-analysis eligible jobs
```

These are the counts used by the Python analysis, PostgreSQL model, SQL queries, DAX measures, KPI validation files, and Power BI dashboard.
