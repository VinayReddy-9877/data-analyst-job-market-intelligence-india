# Data Analyst Job Market Intelligence: Skill, Experience & Salary Analytics — India

An end-to-end Data Analyst portfolio project that converts real Indian analytics job postings into a structured market-intelligence dataset and interactive Power BI reporting layer. The workflow combines Python data preparation, PostgreSQL dimensional modeling, advanced SQL analysis, statistical validation, and Power BI dashboarding.

## Business Problem

Job seekers can see thousands of analyst openings, but it is harder to answer practical questions such as:

- Which analyst roles are hiring most?
- Which technical and analytics skills appear most often?
- Which skills are commonly requested together?
- Which cities and employers account for the most demand?
- What experience levels are explicitly requested?
- How is skill demand changing over time?
- What can advertised salary data support without overstating limited salary coverage?

This project answers those questions through a reproducible analytical pipeline with explicit data-quality and sample-size rules.

## Dataset

- **Market:** India
- **Posting window:** 1 January 2026 to 16 August 2026
- **Observed posting dates:** 2 January 2026 to 16 August 2026
- **Raw source snapshot:** 4,046 unique vacancies
- **Analytical postings:** 4,035
- **Known hiring companies:** 1,364
- **Specific-city locations:** 96
- **Normalized skills:** 44
- **Skill-tagged postings:** 1,744
- **Job-skill relationships:** 6,213
- **Salary-analysis eligible postings:** 110

The raw source snapshot is stored in:

```text
data/raw/job_postings_final_unique_4046.csv
```

The analytical outputs used by SQL, Python, and Power BI are stored in:

```text
data/processed/job_postings_clean.csv
data/processed/job_skills_bridge.csv
```

Missing salary and experience information is preserved rather than imputed.

## Tech Stack

- **Python:** Pandas, NumPy, Matplotlib
- **SQL:** PostgreSQL
- **Data model:** Star schema
- **Statistics:** Bootstrap resampling, descriptive trend analysis
- **Notebook:** Jupyter
- **BI:** Power BI
- **Development:** VS Code, Git

## Analytical Workflow

```text
Real job-posting snapshot
        ↓
Python cleaning + feature engineering
        ↓
Analytical validation
        ↓
Processed jobs + job-skill bridge
        ↓
PostgreSQL star schema
        ↓
Advanced SQL analysis
        ↓
Python EDA + statistical analysis
        ↓
Power BI dashboard
```

## Data Preparation

The analytical pipeline:

- keeps one row per confirmed vacancy,
- standardizes role families, employers, cities and states,
- separates specific-city records from India-level location records,
- extracts explicit experience requirements,
- extracts 44 normalized skills from job titles and descriptions,
- preserves missing experience as `Not Specified`,
- excludes unusable and source-predicted salary values from salary comparisons,
- creates a 90-day comparison window for recent-vs-prior skill analysis,
- and marks complete Monday-Sunday weeks for trend analysis.

The validation layer checks vacancy uniqueness, job-skill bridge integrity, date windows, employer labels, location labels, experience bands, salary eligibility, and complete-week logic.

## PostgreSQL Data Model

The `job_market` schema contains:

### Dimensions

- `dim_role`
- `dim_company`
- `dim_location`
- `dim_date`
- `dim_skill`

### Fact / Bridge

- `fact_jobs`
- `bridge_job_skill`

### Views

- `vw_jobs_enriched`
- `vw_job_skills`

The SQL analysis uses CTEs, window functions, conditional aggregation, percentiles, skill-pair analysis, and descriptive trend calculations.

## Power BI Dashboard

The Power BI project is located at:

```text
dashboard/DataAnalystJobMarketIntelligence.pbix
```

The dashboard contains five report pages:

1. **Executive Overview**
2. **Location & Employer**
3. **Skills & Experience**
4. **Salary Analysis**
5. **Trends & Statistical**

Supporting Power BI files are stored in the same `dashboard/` folder:

```text
dashboard/
├── DataAnalystJobMarketIntelligence.pbix
├── README.md
├── DAX_MEASURES
├── DASHBOARD_CALCULATIONS.md
├── KPI_EXPECTED_VALUES.md
├── POWERBI_ANALYSIS_RESULTS.md
├── POWERBI_VALIDATED_RESULTS.csv
└── Dashboard_Images/
```

### Dashboard Preview

#### Executive Overview

![Executive Overview](dashboard/Dashboard_Images/Executive%20Overview.png)

#### Role & Location

![Role & Location](dashboard/Dashboard_Images/Role%20%26%20Location.png)

#### Skills & Experience

![Skills & Experience](dashboard/Dashboard_Images/Skills%20%26%20Experience.png)

#### Salary Insights

![Salary Insights](dashboard/Dashboard_Images/Salary%20Insights.png)

#### Trends & Statistical

![Trends & Statistical](dashboard/Dashboard_Images/Trends%20%26%20Statistical.png)

## Key Findings

### Role Demand

Business Analyst is the largest role family with **1,541 analytical postings (38.19%)**.

Other high-demand role groups include Data Analyst, Operations / Process, BI Analyst, Risk / Quantitative, and Product Analyst.

### Skill Demand

Among **1,744 skill-tagged postings**:

| Skill | Jobs |
|---|---:|
| SQL | 850 |
| Excel | 624 |
| Power BI | 586 |
| Python | 527 |
| Tableau | 420 |

SQL appears in **48.74% of skill-tagged postings**.

### Skill Co-occurrence

The most common skill combinations are:

- **Python + SQL:** 420 postings
- **Power BI + SQL:** 383
- **Excel + SQL:** 330
- **SQL + Tableau:** 323
- **Power BI + Tableau:** 271

### Location Demand

Specific-city information is available for **3,079 postings (76.31%)**.

Leading cities include:

- **Bengaluru:** 1,073
- **Hyderabad:** 540
- **Mumbai:** 348
- **Pune:** 334
- **Gurugram:** 202

Bengaluru accounts for **34.85% of specific-city postings**.

### Employer Concentration

The top five employers account for **490 postings (12.14%)** of the analytical dataset.

Leading employers include Amazon, Genpact, EXL, Amgen, and JPMorganChase.

### Experience Requirements

Explicit experience information is available for **1,425 postings (35.32%)**.

The remaining **2,610 postings (64.68%)** do not contain a usable minimum-experience requirement and remain labeled `Not Specified`.

`Not Specified` does not mean that no experience is required; it means a usable requirement could not be extracted from the posting.

### Advertised Salary

Only **110 postings (2.73%)** meet the salary-analysis eligibility rules, so salary findings are treated as exploratory.

- **P25:** ₹5.42L
- **Median:** ₹9.50L
- **Mean:** ₹11.64L
- **P75:** ₹16.38L
- **Observed range:** ₹2.70L to ₹42.00L

### SQL and Advertised Salary

Within the validated salary sample:

- **SQL-tagged postings:** n = 18
- **Non-SQL postings:** n = 92
- **Observed median difference:** +₹4.79L
- **50,000-iteration bootstrap 95% interval:** ₹-0.75L to ₹11.00L

Because the interval includes zero, the observed SQL salary difference is **inconclusive** and should not be interpreted as evidence that SQL itself causes higher salary.

### Recent Skill Demand

The recent 90-day window contains **3,480 postings (86.25%)** of the analytical dataset.

Recent skill share examples:

- **SQL:** 21.81%
- **Excel:** 16.01%
- **Power BI:** 14.94%
- **Python:** 13.59%
- **Tableau:** 11.06%

Statistics shows the largest recent-vs-prior share increase among the highlighted skills at **+5.79 percentage points**.

These comparisons are descriptive and are not forecasts.

## Reporting Rules

- Salary values are not imputed.
- Source-predicted salaries are excluded from salary analysis.
- Missing experience remains `Not Specified`.
- Skill counts are based on explicit extracted mentions.
- Trend analysis uses complete Monday-Sunday weeks.
- Recent-vs-prior skill comparisons are descriptive.
- Salary findings are associations, not causal claims.
- Sparse salary coverage is displayed explicitly in the dashboard.

## Repository Structure

```text
Data Analyst Job Market Intelligence Skill, Experience and Salary Analytics — India/
├── dashboard/
│   ├── Dashboard_Images/
│   │   ├── Executive Overview.png
│   │   ├── Role & Location.png
│   │   ├── Salary Insights.png
│   │   ├── Skills & Experience.png
│   │   └── Trends & Statistical.png
│   ├── DataAnalystJobMarketIntelligence.pbix
│   ├── README.md
│   ├── DAX_MEASURES
│   ├── DASHBOARD_CALCULATIONS.md
│   ├── KPI_EXPECTED_VALUES.md
│   ├── POWERBI_ANALYSIS_RESULTS.md
│   └── POWERBI_VALIDATED_RESULTS.csv
├── scripts/
│   ├── build_analytical_dataset.py
│   ├── validate_analysis.py
│   └── load_to_postgres.py
├── data/
│   ├── raw/
│   │   └── job_postings_final_unique_4046.csv
│   └── processed/
│       ├── job_postings_clean.csv
│       └── job_skills_bridge.csv
├── notebooks/
│   └── analysis.ipynb
├── reports/
├── sql/
│   ├── schema.sql
│   └── analysis_queries.sql
├── .gitignore
├── DATA_SOURCE.md
├── README.md
├── RUN_GUIDE.md
└── requirements.txt
```

## Reproduce the Analysis

Create and activate a Python environment, install the dependencies, and run the analytical pipeline from the project root.

```powershell
pip install -r requirements.txt
python .\scripts\build_analytical_dataset.py
python .\scripts\validate_analysis.py
jupyter nbconvert --to notebook --execute ".\notebooks\analysis.ipynb" --inplace
```

For PostgreSQL setup and Power BI connection details, see:

```text
RUN_GUIDE.md
```

The database loader is:

```text
scripts/load_to_postgres.py
```

The SQL schema and analytical queries are:

```text
sql/schema.sql
sql/analysis_queries.sql
```

## Project Outputs

The repository provides:

- reproducible raw-to-analytical data preparation,
- data-quality validation,
- PostgreSQL dimensional modeling,
- advanced SQL analysis,
- Python exploratory and statistical analysis,
- DAX calculations and KPI documentation,
- Power BI analytical reporting,
- validated dashboard results,
- and dashboard images for portfolio and GitHub presentation.

## Notes

Salary availability is limited relative to the full analytical dataset, so salary findings are intentionally presented with coverage and sample-size context.

The project focuses on observed analyst-job demand during the stated collection window and does not treat descriptive trends as forecasts.
